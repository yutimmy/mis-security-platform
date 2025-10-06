from datetime import datetime

from app.models.db import db
from app.models.schema import Post


def test_posts_new_requires_login(client):
    response = client.get("/posts/new")
    assert response.status_code == 302


def test_authenticated_user_can_view_new_post_page(authenticated_client):
    response = authenticated_client.get("/posts/new")
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "id=\"title\"" in content
    assert "id=\"content\"" in content


def test_authenticated_user_can_create_post(authenticated_client, app, test_user):
    payload = {
        "title": "端到端測試文章",
        "content": "# 測試標題\n\n內文",
        "category": "測試",
        "is_published": "1",
    }
    response = authenticated_client.post("/posts/new", data=payload, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        post = Post.query.filter_by(title="端到端測試文章", author_id=test_user).first()
        assert post is not None
        assert post.category == "測試"
        assert post.is_published is True


def test_authenticated_user_can_edit_post(authenticated_client, app, test_user):
    with app.app_context():
        post = Post(
            title="原始標題",
            content="原始內容",
            category="初始",
            author_id=test_user,
            is_published=True,
            created_at=datetime.utcnow(),
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id

    update_payload = {
        "title": "更新後標題",
        "content": "更新內容",
        "category": "更新",
        "is_published": "1",
    }
    response = authenticated_client.post(
        f"/posts/{post_id}/edit", data=update_payload, follow_redirects=True
    )
    assert response.status_code == 200

    with app.app_context():
        updated = Post.query.get(post_id)
        assert updated.title == "更新後標題"
        assert "更新內容" in updated.content


def test_my_posts_page_lists_user_posts(authenticated_client, app, test_user):
    with app.app_context():
        if not Post.query.filter_by(author_id=test_user).first():
            db.session.add(
                Post(
                    title="列表測試文章",
                    content="內容",
                    category="測試",
                    author_id=test_user,
                    is_published=True,
                )
            )
            db.session.commit()

    response = authenticated_client.get("/posts/my-posts")
    assert response.status_code == 200
    assert "我的文章" in response.get_data(as_text=True)
