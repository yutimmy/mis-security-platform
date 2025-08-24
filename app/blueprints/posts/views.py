# Markdown 協作功能 - 文章發布與編輯
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from sqlalchemy import desc

from ...models.db import db
from ...models.schema import Post, User, Image
from ...services.image_service import ImageService


posts_bp = Blueprint('posts', __name__)


@posts_bp.route('/')
def index():
    """文章列表頁"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = Post.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            Post.title.contains(search) | 
            Post.content.contains(search)
        )
    
    posts = query.order_by(desc(Post.updated_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # 取得分類列表
    categories = db.session.query(Post.category).filter(
        Post.is_published == True,
        Post.category.isnot(None)
    ).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('posts/index.html', 
                         posts=posts, 
                         categories=categories,
                         current_category=category,
                         search_query=search)


@posts_bp.route('/<int:post_id>')
def view(post_id):
    """查看文章詳情"""
    post = Post.query.get_or_404(post_id)
    
    # 檢查權限
    if not post.is_published and post.author_id != session.get('user_id'):
        flash('文章不存在或無權限查看', 'error')
        return redirect(url_for('posts.index'))
    
    # 增加查看次數
    post.views = (post.views or 0) + 1
    db.session.commit()
    
    return render_template('posts/view.html', post=post)


@posts_bp.route('/new', methods=['GET', 'POST'])
def create():
    """建立新文章"""
    if not session.get('user_id'):
        flash('請先登入', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            category = request.form.get('category', '').strip()
            is_published = request.form.get('is_published') == '1'
            
            if not title or not content:
                flash('標題和內容為必填項目', 'error')
                return render_template('posts/edit.html')
            
            post = Post(
                title=title,
                content=content,
                category=category if category else None,
                author_id=session['user_id'],
                is_published=is_published,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(post)
            db.session.commit()
            
            flash('文章建立成功', 'success')
            return redirect(url_for('posts.view', post_id=post.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'建立失敗: {str(e)}', 'error')
    
    return render_template('posts/edit.html', post=None)


@posts_bp.route('/<int:post_id>/edit', methods=['GET', 'POST'])
def edit(post_id):
    """編輯文章"""
    if not session.get('user_id'):
        flash('請先登入', 'error')
        return redirect(url_for('auth.login'))
    
    post = Post.query.get_or_404(post_id)
    
    # 檢查權限（只有作者或管理員可以編輯）
    user = User.query.get(session['user_id'])
    if post.author_id != session['user_id'] and user.role != 'admin':
        flash('無權限編輯此文章', 'error')
        return redirect(url_for('posts.view', post_id=post_id))
    
    if request.method == 'POST':
        try:
            post.title = request.form.get('title', '').strip()
            post.content = request.form.get('content', '').strip()
            post.category = request.form.get('category', '').strip() or None
            post.is_published = request.form.get('is_published') == '1'
            post.updated_at = datetime.utcnow()
            
            if not post.title or not post.content:
                flash('標題和內容為必填項目', 'error')
                return render_template('posts/edit.html', post=post)
            
            db.session.commit()
            flash('文章更新成功', 'success')
            return redirect(url_for('posts.view', post_id=post.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')
    
    return render_template('posts/edit.html', post=post)


@posts_bp.route('/<int:post_id>/delete', methods=['POST'])
def delete(post_id):
    """刪除文章"""
    if not session.get('user_id'):
        return jsonify({'code': 1, 'message': '請先登入'})
    
    post = Post.query.get_or_404(post_id)
    
    # 檢查權限
    user = User.query.get(session['user_id'])
    if post.author_id != session['user_id'] and user.role != 'admin':
        return jsonify({'code': 1, 'message': '無權限刪除此文章'})
    
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({'code': 0, 'message': '刪除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 1, 'message': f'刪除失敗: {str(e)}'})


@posts_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """上傳圖片 (for markdown editor)"""
    if not session.get('user_id'):
        return jsonify({'code': 1, 'message': '請先登入'})
    
    if 'image' not in request.files:
        return jsonify({'code': 1, 'message': '未選擇檔案'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '未選擇檔案'})
    
    try:
        image_service = ImageService()
        image_record, message = image_service.upload_image(
            file=file,
            user_id=session['user_id'],
            related_type='post'
        )
        
        if image_record:
            return jsonify({
                'code': 0,
                'message': message,
                'data': {
                    'url': image_service.get_image_url(image_record.id),
                    'id': image_record.id,
                    'filename': image_record.original_filename
                }
            })
        else:
            return jsonify({'code': 1, 'message': message})
            
    except Exception as e:
        return jsonify({'code': 1, 'message': f'上傳失敗: {str(e)}'})


@posts_bp.route('/my-posts')
def my_posts():
    """我的文章列表"""
    if not session.get('user_id'):
        flash('請先登入', 'error')
        return redirect(url_for('auth.login'))
    
    page = request.args.get('page', 1, type=int)
    
    posts = Post.query.filter_by(
        author_id=session['user_id']
    ).order_by(desc(Post.updated_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('posts/my_posts.html', posts=posts)


@posts_bp.route('/api/preview', methods=['POST'])
def preview_markdown():
    """Markdown 預覽 API"""
    # 這裡應該使用安全的 Markdown 解析器
    # 前端可以使用 marked.js + DOMPurify
    content = request.json.get('content', '')
    
    # TODO: 後端也可以用 python-markdown 處理
    # 目前先讓前端處理
    
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': {
            'html': content  # 前端會用 marked.js 轉換
        }
    })
