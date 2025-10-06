from datetime import datetime, timezone

from utils.timezone_utils import (
    format_datetime,
    get_current_time,
    get_timezone_offset,
    local_to_utc,
    now_with_tz,
    utc_to_local,
)


def test_timezone_offset_for_asia_taipei():
    offset = get_timezone_offset("Asia/Taipei")
    assert offset.total_seconds() == 8 * 3600


def test_now_with_tz_returns_timezone_aware_datetime():
    current = now_with_tz("Asia/Taipei")
    assert current.tzinfo is not None
    assert current.utcoffset().total_seconds() == 8 * 3600


def test_get_current_time_returns_naive_local_datetime():
    current = get_current_time("Asia/Taipei")
    assert current.tzinfo is None


def test_utc_to_local_and_back_roundtrip():
    utc_dt = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    local_dt = utc_to_local(utc_dt, "Asia/Taipei")
    assert local_dt.tzinfo is not None
    assert local_dt.hour == 20  # UTC+8

    roundtrip = local_to_utc(local_dt, "Asia/Taipei")
    assert roundtrip.tzinfo == timezone.utc
    assert roundtrip.hour == 12


def test_format_datetime_handles_timezone_conversion():
    utc_dt = datetime(2025, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    formatted = format_datetime(utc_dt, "%Y-%m-%d %H:%M", "Asia/Taipei")
    assert formatted == "2025-10-05 20:00"

    naive_dt = datetime(2025, 10, 5, 8, 0, 0)
    assert format_datetime(naive_dt, "%H:%M") == "08:00"
