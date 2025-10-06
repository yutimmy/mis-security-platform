# 時區處理工具
from datetime import datetime, timezone, timedelta


def get_timezone_offset(tz_name):
    """
    取得時區偏移量
    
    Args:
        tz_name: 時區名稱（如 'Asia/Taipei'）
    
    Returns:
        timedelta: 時區偏移量
    """
    # 常見時區對應表
    tz_offsets = {
        'Asia/Taipei': timedelta(hours=8),
        'Asia/Shanghai': timedelta(hours=8),
        'Asia/Tokyo': timedelta(hours=9),
        'Asia/Singapore': timedelta(hours=8),
        'UTC': timedelta(hours=0),
        'America/New_York': timedelta(hours=-5),  # 冬令時間
        'America/Los_Angeles': timedelta(hours=-8),  # 冬令時間
        'Europe/London': timedelta(hours=0),  # 冬令時間
    }
    
    return tz_offsets.get(tz_name, timedelta(hours=0))


def now_with_tz(tz_name='Asia/Taipei'):
    """
    取得當前時區的時間
    
    Args:
        tz_name: 時區名稱（預設 'Asia/Taipei' 即 UTC+8）
    
    Returns:
        datetime: 帶時區資訊的當前時間
    """
    offset = get_timezone_offset(tz_name)
    tz = timezone(offset)
    return datetime.now(tz)


def get_current_time(tz_name='Asia/Taipei'):
    """
    取得當前時間（naive datetime，用於資料庫儲存）
    這個函數返回的時間已經是本地時區，但沒有 tzinfo
    適合直接存入資料庫
    
    Args:
        tz_name: 時區名稱（預設 'Asia/Taipei' 即 UTC+8）
    
    Returns:
        datetime: 當前本地時間（無時區資訊）
    """
    offset = get_timezone_offset(tz_name)
    tz = timezone(offset)
    return datetime.now(tz).replace(tzinfo=None)


def utc_to_local(dt, tz_name='Asia/Taipei'):
    """
    將 UTC 時間轉換為本地時間
    
    Args:
        dt: UTC datetime 物件
        tz_name: 目標時區名稱
    
    Returns:
        datetime: 本地時間
    """
    if dt is None:
        return None
    
    # 如果已有時區資訊，先轉換為 UTC
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        # 假設輸入是 UTC 時間
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 轉換到目標時區
    offset = get_timezone_offset(tz_name)
    target_tz = timezone(offset)
    return dt.astimezone(target_tz)


def local_to_utc(dt, tz_name='Asia/Taipei'):
    """
    將本地時間轉換為 UTC 時間
    
    Args:
        dt: 本地 datetime 物件
        tz_name: 來源時區名稱
    
    Returns:
        datetime: UTC 時間
    """
    if dt is None:
        return None
    
    # 如果沒有時區資訊，加上來源時區
    if dt.tzinfo is None:
        offset = get_timezone_offset(tz_name)
        source_tz = timezone(offset)
        dt = dt.replace(tzinfo=source_tz)
    
    # 轉換為 UTC
    return dt.astimezone(timezone.utc)


def format_datetime(dt, fmt='%Y-%m-%d %H:%M:%S', tz_name='Asia/Taipei'):
    """
    格式化時間並轉換為指定時區
    
    Args:
        dt: datetime 物件
        fmt: 格式字串
        tz_name: 目標時區名稱
    
    Returns:
        str: 格式化後的時間字串
    """
    if dt is None:
        return ''
    
    # 如果沒有時區資訊，假設是資料庫存的本地時間
    if dt.tzinfo is None:
        return dt.strftime(fmt)
    
    # 如果有時區資訊，轉換為本地時間
    local_dt = utc_to_local(dt, tz_name)
    return local_dt.strftime(fmt)
