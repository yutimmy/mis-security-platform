# 身分認證：註冊/登入/登出
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import bcrypt

from app.models.db import db
from app.models.schema import User


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """使用者註冊"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # 基本驗證
        if not username or not email or not password:
            flash('所有欄位都是必填的', 'error')
            return render_template('auth/register.html')
        
        # 檢查使用者是否已存在
        if User.query.filter_by(username=username).first():
            flash('使用者名稱已存在', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email 已存在', 'error')
            return render_template('auth/register.html')
        
        # 建立新使用者
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_active=False  # 需要管理員審核
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('註冊成功！請等待管理員審核', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """使用者登入"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('請輸入帳號和密碼', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('帳號不存在', 'error')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('帳號尚未啟用，請聯繫管理員', 'error')
            return render_template('auth/login.html')
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            flash('密碼錯誤', 'error')
            return render_template('auth/login.html')
        
        # 設定 session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        flash(f'歡迎 {user.username}！', 'success')
        
        # 根據角色導向不同頁面
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('public.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """使用者登出"""
    session.clear()
    flash('已成功登出', 'info')
    return redirect(url_for('public.index'))
