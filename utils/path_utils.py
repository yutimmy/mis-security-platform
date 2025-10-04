# 路徑工具函數 - 確保所有腳本使用一致的數據庫路徑
import logging
import os
import sys
from pathlib import Path

from .logging_config import configure_logging, get_logger


logger = get_logger(__name__)


def get_project_root():
    """獲取專案根目錄的絕對路徑"""
    # 如果是在專案內的任何位置執行，都要回到根目錄
    current_file = Path(__file__).resolve()
    
    # 向上查找包含 config.py 的目錄作為專案根目錄
    current_dir = current_file.parent
    while current_dir != current_dir.parent:
        if (current_dir / "config.py").exists():
            return str(current_dir)
        current_dir = current_dir.parent
    
    # 如果找不到，使用當前檔案的上一層目錄
    return str(current_file.parent.parent)


def ensure_project_path():
    """確保專案根目錄在 Python 路徑中，並切換工作目錄"""
    project_root = get_project_root()
    
    # 添加專案根目錄到 Python 路徑
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 切換工作目錄到專案根目錄
    os.chdir(project_root)
    
    return project_root


def get_database_path():
    """獲取數據庫檔案的絕對路徑"""
    ensure_project_path()
    
    try:
        from config import Config
        return Config.SQLITE_PATH
    except ImportError:
        # 如果無法導入 config，使用預設路徑
        project_root = get_project_root()
        return os.path.join(project_root, "data", "app.db")


if __name__ == "__main__":
    # 測試功能
    configure_logging()
    logger.info("專案根目錄: %s", get_project_root())
    logger.info("當前工作目錄: %s", os.getcwd())
    ensure_project_path()
    logger.info("切換後工作目錄: %s", os.getcwd())
    logger.info("數據庫路徑: %s", get_database_path())
