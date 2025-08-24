# 圖片上傳服務
import os
import hashlib
import uuid
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

from ..models.db import db
from ..models.schema import Image


class ImageService:
    """圖片上傳與管理服務"""

    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/images')
        self.allowed_types = current_app.config.get('ALLOWED_IMAGE_TYPES', 'image/png,image/jpeg,image/webp').split(',')
        self.max_size_mb = current_app.config.get('MAX_IMAGE_SIZE_MB', 1.5)

    def upload_image(self, file, user_id, related_type=None, related_id=None):
        """上傳圖片"""
        try:
            # 驗證檔案
            if not self._validate_file(file):
                return None, "檔案驗證失敗"

            # 確保上傳目錄存在
            os.makedirs(self.upload_folder, exist_ok=True)

            # 產生唯一檔名
            file_ext = self._get_file_extension(file.filename)
            file_hash = self._generate_file_hash(file)
            filename = f"{file_hash}_{uuid.uuid4().hex[:8]}{file_ext}"
            file_path = os.path.join(self.upload_folder, filename)

            # 檢查是否已存在相同檔案
            existing_image = Image.query.filter_by(file_hash=file_hash).first()
            if existing_image:
                return existing_image, "檔案已存在"

            # 儲存檔案
            file.seek(0)  # 重置檔案指標
            file.save(file_path)

            # 處理圖片（壓縮、產生縮圖等）
            processed_info = self._process_image(file_path)

            # 記錄到資料庫
            image_record = Image(
                filename=filename,
                original_filename=secure_filename(file.filename),
                file_path=file_path,
                file_hash=file_hash,
                file_size=os.path.getsize(file_path),
                mime_type=file.content_type,
                width=processed_info.get('width'),
                height=processed_info.get('height'),
                uploaded_by=user_id,
                related_type=related_type,
                related_id=related_id,
                created_at=datetime.utcnow()
            )

            db.session.add(image_record)
            db.session.commit()

            return image_record, "上傳成功"

        except Exception as e:
            current_app.logger.error(f"Image upload failed: {str(e)}")
            db.session.rollback()
            return None, f"上傳失敗: {str(e)}"

    def delete_image(self, image_id, user_id):
        """刪除圖片"""
        try:
            image = Image.query.filter_by(id=image_id).first()
            if not image:
                return False, "圖片不存在"

            # 檢查權限（只有上傳者或管理員可以刪除）
            # TODO: 加入角色權限檢查

            # 刪除實際檔案
            if os.path.exists(image.file_path):
                os.remove(image.file_path)

            # 從資料庫刪除
            db.session.delete(image)
            db.session.commit()

            return True, "刪除成功"

        except Exception as e:
            current_app.logger.error(f"Image deletion failed: {str(e)}")
            db.session.rollback()
            return False, f"刪除失敗: {str(e)}"

    def get_image_url(self, image_id):
        """取得圖片 URL"""
        image = Image.query.filter_by(id=image_id).first()
        if not image:
            return None

        # 相對於靜態檔案的路徑
        relative_path = image.file_path.replace('static/', '')
        return f"/{relative_path}"

    def get_user_images(self, user_id, page=1, per_page=20):
        """取得使用者上傳的圖片"""
        return Image.query.filter_by(
            uploaded_by=user_id
        ).order_by(
            Image.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def _validate_file(self, file):
        """驗證檔案"""
        if not file or not file.filename:
            return False

        # 檢查 MIME 類型
        if file.content_type not in self.allowed_types:
            return False

        # 檢查檔案大小
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        
        if size_mb > self.max_size_mb:
            return False

        return True

    def _get_file_extension(self, filename):
        """取得檔案副檔名"""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''

    def _generate_file_hash(self, file):
        """產生檔案雜湊值"""
        file.seek(0)
        file_hash = hashlib.md5(file.read()).hexdigest()
        file.seek(0)
        return file_hash

    def _process_image(self, file_path):
        """處理圖片（壓縮、取得尺寸等）"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size

                # 如果圖片過大，進行壓縮
                max_dimension = 1920
                if width > max_dimension or height > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    img.save(file_path, optimize=True, quality=85)
                    width, height = img.size

                return {
                    'width': width,
                    'height': height,
                    'processed': True
                }

        except Exception as e:
            current_app.logger.error(f"Image processing failed: {str(e)}")
            return {
                'width': None,
                'height': None,
                'processed': False
            }
