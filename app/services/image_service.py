# 圖片上傳服務
import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename

from ..models.db import db
from ..models.schema import Image


class ImageService:
    """圖片上傳與管理服務"""

    def __init__(self):
        uploads_config = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/images')
        self.app_root = Path(current_app.root_path)
        self.upload_root = self.app_root / uploads_config
        self.relative_upload_root = Path(uploads_config)

        allowed_types_config = current_app.config.get('ALLOWED_IMAGE_TYPES', 'image/png,image/jpeg,image/webp')
        self.allowed_mime_types = {
            mime.strip().lower()
            for mime in allowed_types_config.split(',')
            if mime.strip()
        }
        self.allowed_extensions = {
            ext
            for ext in (self._extension_from_mime(mime) for mime in self.allowed_mime_types)
            if ext
        }
        self.max_size_mb = current_app.config.get('MAX_IMAGE_SIZE_MB', 1.5)

    def upload_image(self, file, user_id, related_type=None, related_id=None):
        """上傳圖片"""
        is_valid, error_message, metadata = self._validate_file(file)
        if not is_valid:
            return None, error_message

        detected_mime = metadata['mime']
        file_ext = metadata['extension']
        absolute_path = None

        try:
            # 確保上傳目錄存在
            self.upload_root.mkdir(parents=True, exist_ok=True)

            # 產生唯一檔名
            file_hash = self._generate_file_hash(file)
            filename = f"{file_hash}_{uuid.uuid4().hex[:8]}{file_ext}"
            absolute_path = self.upload_root / filename
            relative_path = self.relative_upload_root / filename

            # 檢查是否已存在相同檔案
            existing_image = Image.query.filter(Image.file_path.contains(file_hash)).first()
            if existing_image:
                return existing_image, "檔案已存在"

            # 儲存檔案
            file.seek(0)
            file.save(absolute_path)

            # 處理圖片（壓縮、產生縮圖等）
            processed_info = self._process_image(absolute_path)
            if not processed_info.get('processed'):
                raise ValueError(processed_info.get('error') or '圖片處理失敗')

            # 記錄到資料庫
            image_record = Image(
                original_filename=secure_filename(file.filename),
                file_path=str(relative_path).replace('\\', '/'),
                file_size=os.path.getsize(absolute_path),
                mime_type=detected_mime,
                width=processed_info.get('width'),
                height=processed_info.get('height'),
                user_id=user_id,
                related_type=related_type,
                related_id=related_id,
                post_id=related_id if related_type == 'post' else None,
                created_at=datetime.utcnow()
            )

            db.session.add(image_record)
            db.session.commit()

            return image_record, "上傳成功"

        except Exception as e:
            current_app.logger.error(f"Image upload failed: {str(e)}")
            db.session.rollback()
            if absolute_path and absolute_path.exists():
                try:
                    absolute_path.unlink()
                except OSError:
                    current_app.logger.warning("Failed to remove incomplete upload %s", absolute_path)
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
            absolute_path = (self.app_root / image.file_path).resolve()
            if absolute_path.exists():
                absolute_path.unlink()

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
        return f"/{relative_path}" if not relative_path.startswith('/') else relative_path

    def get_user_images(self, user_id, page=1, per_page=20):
        """取得使用者上傳的圖片"""
        return Image.query.filter_by(
            user_id=user_id
        ).order_by(
            Image.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def _validate_file(self, file):
        """驗證檔案內容與大小"""
        if not file or not file.filename:
            return False, "未選擇檔案", None

        stream = file.stream
        stream.seek(0, os.SEEK_END)
        size_mb = stream.tell() / (1024 * 1024)
        stream.seek(0)

        if size_mb <= 0:
            return False, "檔案內容為空", None
        if size_mb > self.max_size_mb:
            return False, f"檔案大小超過 {self.max_size_mb}MB 限制", None

        try:
            stream.seek(0)
            with Image.open(stream) as img:
                img.verify()
                format_name = img.format
                detected_mime = Image.MIME.get(format_name)
        except Exception:
            stream.seek(0)
            return False, "檔案不是有效的圖片", None

        stream.seek(0)

        if not detected_mime or detected_mime.lower() not in self.allowed_mime_types:
            return False, "圖片格式不支援", None

        extension = self._extension_from_format(format_name)
        if not extension or (self.allowed_extensions and extension not in self.allowed_extensions):
            return False, "圖片副檔名不支援", None

        return True, None, {
            'mime': detected_mime.lower(),
            'extension': extension
        }

    def _extension_from_mime(self, mime):
        mapping = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp'
        }
        return mapping.get(mime.lower())

    def _extension_from_format(self, format_name):
        if not format_name:
            return None
        mapping = {
            'JPEG': '.jpg',
            'JPG': '.jpg',
            'PNG': '.png',
            'WEBP': '.webp'
        }
        return mapping.get(format_name.upper())

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
                    'processed': True,
                    'error': None
                }

        except Exception as e:
            current_app.logger.error(f"Image processing failed: {str(e)}")
            return {
                'width': None,
                'height': None,
                'processed': False,
                'error': str(e)
            }
