import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import unicodedata

def convert_chrome_time(chrome_time):
    """Chuyển đổi thời gian Chrome/Brave (microseconds từ 1601-01-01)."""
    if chrome_time is None or chrome_time <= 0:
        return ""
    try:
        epoch_start = datetime(1601, 1, 1)
        delta = chrome_time / 1000000
        result = epoch_start + timedelta(seconds=delta)
        if result.year < 2000 or result.year > 2030:
            return ""
        return result.strftime("%m/%d/%Y %H:%M:%S")
    except (ValueError, OverflowError, TypeError):
        return ""

def clean_string(s):
    """Làm sạch chuỗi để tránh lỗi ký tự trong CSV."""
    if pd.isna(s):
        return "Không xác định"
    s = unicodedata.normalize('NFKC', str(s))
    return ''.join(c for c in s if c.isprintable())

def table_exists(cursor, table_name):
    """Kiểm tra bảng tồn tại trong cơ sở dữ liệu."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def read_brave_data(conn, cursor, db_type, limit, data_type="all", page=1, items_per_page=20):
    """Đọc dữ liệu từ cơ sở dữ liệu Brave."""
    all_data = []
    errors = []
    offset = (page - 1) * items_per_page
    max_total_records = items_per_page

    if db_type == "History":
        if data_type in ["all", "history"] and table_exists(cursor, "urls"):
            cursor.execute("""
                SELECT urls.url, urls.title, urls.visit_count, visits.visit_time
                FROM urls JOIN visits ON urls.id = visits.url  -- Sửa visits.url_id thành visits.url
                ORDER BY visits.visit_time DESC
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Lịch sử",
                "URL": clean_string(row[0]),
                "Tiêu đề": clean_string(row[1]) or "Không có tiêu đề",
                "Số lần truy cập": row[2],
                "Thời gian": convert_chrome_time(row[3])
            } for row in cursor.fetchall()])
        elif data_type == "history":
            errors.append("Bảng urls hoặc visits không tồn tại.")

        if data_type in ["all", "downloads"] and table_exists(cursor, "downloads"):
            cursor.execute("""
                SELECT target_path, referrer, start_time
                FROM downloads
                ORDER BY start_time DESC
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Tải xuống",
                "URL": clean_string(row[1]) or "Không có nguồn",
                "Tiêu đề": clean_string(row[0]) or "Không có đường dẫn",
                "Số lần truy cập": None,
                "Thời gian": convert_chrome_time(row[2])
            } for row in cursor.fetchall()])
        elif data_type == "downloads":
            errors.append("Bảng downloads không tồn tại.")

    if db_type == "Cookies":
        if data_type in ["all", "cookies"] and table_exists(cursor, "cookies"):
            cursor.execute("""
                SELECT name, value, host, path, expires_utc
                FROM cookies
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Cookie",
                "URL": clean_string(row[2]),
                "Tiêu đề": f"Cookie: {clean_string(row[0])}",
                "Số lần truy cập": None,
                "Thời gian": convert_chrome_time(row[4])
            } for row in cursor.fetchall()])
        elif data_type == "cookies":
            errors.append("Bảng cookies không tồn tại.")

    if db_type == "Logins":
        if data_type in ["all", "logins"] and table_exists(cursor, "logins"):
            cursor.execute("""
                SELECT origin_url, username_value, password_value, date_created
                FROM logins
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Đăng nhập",
                "URL": clean_string(row[0]),
                "Tiêu đề": f"Tên người dùng: {clean_string(row[1])}",
                "Số lần truy cập": None,
                "Thời gian": convert_chrome_time(row[3])
            } for row in cursor.fetchall()])
        elif data_type == "logins":
            errors.append("Bảng logins không tồn tại.")

    if db_type == "Autofill":
        if data_type in ["all", "autofill"] and table_exists(cursor, "autofill"):
            cursor.execute("""
                SELECT name, value, date_created
                FROM autofill
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Tự động điền",
                "URL": "Không có URL",
                "Tiêu đề": f"{clean_string(row[0])}: {clean_string(row[1])}",
                "Số lần truy cập": None,
                "Thời gian": convert_chrome_time(row[2])
            } for row in cursor.fetchall()])
        elif data_type == "autofill":
            errors.append("Bảng autofill không tồn tại.")

    return all_data, errors

def calculate_total_records(cursor, db_type, data_type):
    """Tính tổng số bản ghi cho Brave."""
    total_records = 0
    if db_type == "History":
        if data_type in ["all", "history"] and table_exists(cursor, "urls"):
            cursor.execute("SELECT COUNT(*) FROM urls JOIN visits ON urls.id = visits.url")  # Sửa visits.url_id thành visits.url
            total_records += cursor.fetchone()[0]
        if data_type in ["all", "downloads"] and table_exists(cursor, "downloads"):
            cursor.execute("SELECT COUNT(*) FROM downloads")
            total_records += cursor.fetchone()[0]
    if db_type == "Cookies":
        if data_type in ["all", "cookies"] and table_exists(cursor, "cookies"):
            cursor.execute("SELECT COUNT(*) FROM cookies")
            total_records += cursor.fetchone()[0]
    if db_type == "Logins":
        if data_type in ["all", "logins"] and table_exists(cursor, "logins"):
            cursor.execute("SELECT COUNT(*) FROM logins")
            total_records += cursor.fetchone()[0]
    if db_type == "Autofill":
        if data_type in ["all", "autofill"] and table_exists(cursor, "autofill"):
            cursor.execute("SELECT COUNT(*) FROM autofill")
            total_records += cursor.fetchone()[0]
    return total_records