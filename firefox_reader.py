import sqlite3
from datetime import datetime, timedelta
import json
import pandas as pd
import unicodedata

def convert_firefox_time(firefox_time):
    """Chuyển đổi thời gian Firefox (microseconds từ 1970-01-01)."""
    if firefox_time is None or firefox_time <= 0:
        return ""
    try:
        epoch_start = datetime(1970, 1, 1)
        delta = firefox_time / 1000000
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

def read_firefox_data(db_path, db_type, conn, cursor, limit, data_type="all", page=1, items_per_page=20):
    """Đọc dữ liệu từ cơ sở dữ liệu Firefox."""
    all_data = []
    errors = []
    offset = (page - 1) * items_per_page
    max_total_records = items_per_page

    if db_type == "Logins":
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                logins_data = json.load(f)
            if "logins" in logins_data:
                for login in logins_data["logins"]:
                    all_data.append({
                        "Loại": "Đăng nhập",
                        "URL": login.get("hostname", "Không có URL"),
                        "Tiêu đề": f"Tên người dùng: {login.get('username', 'Không có tên')}",
                        "Số lần truy cập": None,
                        "Thời gian": datetime.fromtimestamp(login.get("timeCreated", 0) / 1000).strftime("%m/%d/%Y %H:%M:%S") if login.get("timeCreated") else "Không có thời gian"
                    })
            total_records = len(all_data)
            all_data = all_data[offset:offset + items_per_page]
            total_pages = (total_records + items_per_page - 1) // items_per_page
            return {
                "data": all_data,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "total_records": total_records
            }, None
        except Exception as e:
            return None, f"Lỗi khi đọc logins.json: {e}"

    if db_type == "History":
        if data_type in ["all", "history"] and table_exists(cursor, "moz_places"):
            cursor.execute("""
                SELECT url, title, visit_count, last_visit_date
                FROM moz_places
                WHERE url IS NOT NULL
                ORDER BY last_visit_date DESC
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Lịch sử",
                "URL": clean_string(row[0]),
                "Tiêu đề": clean_string(row[1]) or "Không có tiêu đề",
                "Số lần truy cập": row[2],
                "Thời gian": convert_firefox_time(row[3])
            } for row in cursor.fetchall()])
        elif data_type == "history":
            errors.append("Bảng moz_places không tồn tại.")

        if data_type in ["all", "downloads"] and table_exists(cursor, "moz_downloads"):
            cursor.execute("""
                SELECT name, source, startTime
                FROM moz_downloads
                ORDER BY startTime DESC
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Tải xuống",
                "URL": clean_string(row[1]) or "Không có nguồn",
                "Tiêu đề": clean_string(row[0]) or "Không có tên file",
                "Số lần truy cập": None,
                "Thời gian": convert_firefox_time(row[2])
            } for row in cursor.fetchall()])
        elif data_type == "downloads":
            errors.append("Bảng moz_downloads không tồn tại hoặc Firefox không có dữ liệu tải xuống.")

    if db_type == "Cookies":
        if data_type in ["all", "cookies"] and table_exists(cursor, "moz_cookies"):
            cursor.execute("""
                SELECT name, value, host, path, expiry
                FROM moz_cookies
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Cookie",
                "URL": clean_string(row[2]),
                "Tiêu đề": f"Cookie: {clean_string(row[0])}",
                "Số lần truy cập": None,
                "Thời gian": datetime.fromtimestamp(row[4]).strftime("%m/%d/%Y %H:%M:%S") if row[4] else "Không có thời gian"
            } for row in cursor.fetchall()])
        elif data_type == "cookies":
            errors.append("Bảng moz_cookies không tồn tại.")

    if db_type == "Formhistory":
        if data_type in ["all", "autofill"] and table_exists(cursor, "moz_formhistory"):
            cursor.execute("""
                SELECT fieldname, value
                FROM moz_formhistory
                LIMIT ? OFFSET ?
            """, (max_total_records, offset))
            all_data.extend([{
                "Loại": "Tự động điền",
                "URL": "Không có URL",
                "Tiêu đề": f"{clean_string(row[0])}: {clean_string(row[1])}",
                "Số lần truy cập": None,
                "Thời gian": "Không có thời gian"
            } for row in cursor.fetchall()])
        elif data_type == "autofill":
            errors.append("Bảng moz_formhistory không tồn tại.")

    return all_data, errors

def calculate_total_records(cursor, db_type, data_type):
    """Tính tổng số bản ghi cho Firefox."""
    total_records = 0
    if db_type == "History":
        if data_type in ["all", "history"] and table_exists(cursor, "moz_places"):
            cursor.execute("SELECT COUNT(*) FROM moz_places WHERE url IS NOT NULL")
            total_records += cursor.fetchone()[0]
        if data_type in ["all", "downloads"] and table_exists(cursor, "moz_downloads"):
            cursor.execute("SELECT COUNT(*) FROM moz_downloads")
            total_records += cursor.fetchone()[0]
    if db_type == "Cookies":
        if data_type in ["all", "cookies"] and table_exists(cursor, "moz_cookies"):
            cursor.execute("SELECT COUNT(*) FROM moz_cookies")
            total_records += cursor.fetchone()[0]
    if db_type == "Formhistory":
        if data_type in ["all", "autofill"] and table_exists(cursor, "moz_formhistory"):
            cursor.execute("SELECT COUNT(*) FROM moz_formhistory")
            total_records += cursor.fetchone()[0]
    return total_records