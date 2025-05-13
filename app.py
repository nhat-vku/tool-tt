import sqlite3
import os
import shutil
import tempfile
import pandas as pd
import platform
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session
import unicodedata
from edge_reader import (
    read_edge_data,
    calculate_total_records as calculate_edge_records,
)
from firefox_reader import (
    read_firefox_data,
    calculate_total_records as calculate_firefox_records,
)
from brave_reader import (
    read_brave_data,
    calculate_total_records as calculate_brave_records,
)
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def clean_string(s):
    """Làm sạch chuỗi để tránh lỗi ký tự trong CSV."""
    if pd.isna(s):
        return "Không xác định"
    s = unicodedata.normalize("NFKC", str(s))
    return "".join(c for c in s if c.isprintable())


def get_firefox_profile(user_home, os_type):
    """Tìm thư mục profile mặc định của Firefox."""
    profiles_dir = {
        "windows": user_home
        / "AppData"
        / "Roaming"
        / "Mozilla"
        / "Firefox"
        / "Profiles",
    }.get(os_type)

    if not profiles_dir or not profiles_dir.exists():
        return None, "Thư mục profile Firefox không tồn tại."

    for profile in profiles_dir.iterdir():
        if profile.is_dir() and (profile / "places.sqlite").exists():
            return profile, None
    return None, "Không tìm thấy profile Firefox hợp lệ."


def get_browser_db_path(browser, user_home, profile="Default", db_type="History"):
    """Lấy đường dẫn cơ sở dữ liệu SQLite của trình duyệt."""
    os_type = (
        "windows"
        if platform.system() == "Windows"
        else "macos" if platform.system() == "Darwin" else "linux"
    )

    if not user_home.exists():
        return None, f"Thư mục home không tồn tại: {user_home}"

    browser = browser.lower()
    if browser not in ["edge", "firefox", "brave"]:
        return None, f"Trình duyệt không được hỗ trợ: {browser}"

    if browser == "firefox":
        profile_dir, error = get_firefox_profile(user_home, os_type)
        if not profile_dir:
            return None, error
        db_paths = {
            "History": profile_dir / "places.sqlite",
            "Cookies": profile_dir / "cookies.sqlite",
            "Formhistory": profile_dir / "formhistory.sqlite",
            "Logins": profile_dir / "logins.json",
        }
        db_path = db_paths.get(db_type)
        if not db_path:
            return None, f"Loại cơ sở dữ liệu không được hỗ trợ cho Firefox: {db_type}"
        return db_path, None

    browser_paths = {
        "edge": {
            "windows": {
                "History": user_home
                / "AppData"
                / "Local"
                / "Microsoft"
                / "Edge"
                / "User Data"
                / profile
                / "History",
                "Cookies": user_home
                / "AppData"
                / "Local"
                / "Microsoft"
                / "Edge"
                / "User Data"
                / profile
                /"Network"
                / "Cookies",
                "Logins": user_home
                / "AppData"
                / "Local"
                / "Microsoft"
                / "Edge"
                / "User Data"
                / profile
                / "Login Data",
                "Autofill": user_home
                / "AppData"
                / "Local"
                / "Microsoft"
                / "Edge"
                / "User Data"
                / profile
                / "Web Data",
            }
        },
        "brave": {
            "windows": {
                "History": user_home
                / "AppData"
                / "Local"
                / "BraveSoftware"
                / "Brave-Browser"
                / "User Data"
                / profile
                / "History",
                "Cookies": user_home
                / "AppData"
                / "Local"
                / "BraveSoftware"
                / "Brave-Browser"
                / "User Data"
                / profile
                /"Network"
                / "Cookies",
                "Logins": user_home
                / "AppData"
                / "Local"
                / "BraveSoftware"
                / "Brave-Browser"
                / "User Data"
                / profile
                / "Login Data",
                "Autofill": user_home
                / "AppData"
                / "Local"
                / "BraveSoftware"
                / "Brave-Browser"
                / "User Data"
                / profile
                / "Web Data",
            }
        },
    }

    db_path = browser_paths.get(browser, {}).get(os_type, {}).get(db_type)
    if not db_path:
        return (
            None,
            f"Hệ điều hành hoặc loại cơ sở dữ liệu không được hỗ trợ cho {browser}: {os_type}, {db_type}",
        )

    return db_path, None


def copy_db_to_temp(db_path):
    """Sao chép cơ sở dữ liệu sang thư mục tạm."""
    temp_dir = Path(tempfile.gettempdir())
    temp_db = temp_dir / f"browser_data_{os.urandom(4).hex()}.db"
    try:
        shutil.copy2(db_path, temp_db)
        return temp_db, None
    except Exception as e:
        return None, f"Không thể sao chép cơ sở dữ liệu: {e}"


def read_browser_data(
    db_path, db_type, browser, limit, data_type="all", page=1, items_per_page=20
):
    """Đọc dữ liệu từ cơ sở dữ liệu của trình duyệt."""
    if browser == "firefox" and db_type == "Logins":
        result = read_firefox_data(
            db_path, db_type, None, None, limit, data_type, page, items_per_page
        )
        return result

    temp_db, error = copy_db_to_temp(db_path)
    if not temp_db:
        return None, error

    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        if browser == "edge":
            all_data, errors = read_edge_data(
                conn, cursor, db_type, limit, data_type, page, items_per_page
            )
            total_records = calculate_edge_records(cursor, db_type, data_type)
        elif browser == "firefox":
            all_data, errors = read_firefox_data(
                db_path, db_type, conn, cursor, limit, data_type, page, items_per_page
            )
            total_records = calculate_firefox_records(cursor, db_type, data_type)
        elif browser == "brave":
            all_data, errors = read_brave_data(
                conn, cursor, db_type, limit, data_type, page, items_per_page
            )
            total_records = calculate_brave_records(cursor, db_type, data_type)

        if not all_data and errors:
            return None, f"Không tìm thấy dữ liệu. Lỗi: {', '.join(errors)}"
        if not all_data:
            return (
                None,
                f"Không tìm thấy dữ liệu cho loại {data_type} trên {browser.capitalize()}.",
            )

        total_records = min(total_records, limit)
        total_pages = (total_records + items_per_page - 1) // items_per_page

        return {
            "data": all_data,
            "total_pages": total_pages,
            "current_page": page,
            "items_per_page": items_per_page,
            "total_records": total_records,
        }, None

    except sqlite3.Error as e:
        return None, f"Lỗi cơ sở dữ liệu: {e}"
    except Exception as e:
        return None, f"Lỗi không xác định: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        if temp_db and os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except:
                pass


def save_to_csv(data, output_file):
    """Lưu dữ liệu vào file CSV với mã hóa UTF-8 BOM."""
    if not data or len(data) == 0:
        return False, "Không có dữ liệu để lưu vào CSV."
    try:
        df = pd.DataFrame(data)
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(clean_string)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        return True, output_file
    except Exception as e:
        return False, f"Lỗi khi lưu CSV: {e}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST", "GET"])
def preview():
    browser = session.get("browser")
    limit = session.get("limit")
    data_type = session.get("data_type")

    page = int(request.args.get("page", 1))
    items_per_page = 20

    if request.method == "POST":
        browser = request.form.get("browser")
        limit = int(request.form.get("limit", 100))
        data_type = request.form.get("data_type")

        if not browser or limit < 1 or limit > 1000 or not data_type:
            return jsonify({"error": "Dữ liệu không hợp lệ, vui lòng kiểm tra lại."})

        session["browser"] = browser
        session["limit"] = limit
        session["data_type"] = data_type

    elif request.method == "GET":
        if not browser or not limit or not data_type:
            return jsonify({"error": "Vui lòng gửi dữ liệu form trước khi phân trang."})

    user_home = Path.home()

    db_types = {
        "history": "History",
        "downloads": "History",
        "cookies": "Cookies",
        "logins": "Logins",
        "autofill": "Autofill",
        "all": "History",
    }
    db_type = db_types.get(data_type, "History")

    db_path, error = get_browser_db_path(browser, user_home, db_type=db_type)

    if not db_path:
        return jsonify(
            {"error": error or f"Không thể lấy đường dẫn cơ sở dữ liệu cho {browser}."}
        )

    if not db_path.exists():
        return jsonify(
            {
                "error": f"File cơ sở dữ liệu không tồn tại: {db_path}. Đảm bảo trình duyệt đã được cài đặt và có dữ liệu."
            }
        )

    data, error = read_browser_data(
        db_path, db_type, browser, limit, data_type, page, items_per_page
    )
    if not data:
        return jsonify({"error": error or "Không thể trích xuất dữ liệu."})

    return jsonify(data)


@app.route("/download", methods=["POST"])
def download():
    browser = request.form.get("browser")
    limit = int(request.form.get("limit", 100))
    data_type = request.form.get("data_type")

    if not browser or limit < 1 or limit > 1000 or not data_type:
        return jsonify({"error": "Dữ liệu không hợp lệ, vui lòng kiểm tra lại."})

    user_home = Path.home()

    db_types = {
        "history": "History",
        "downloads": "History",
        "cookies": "Cookies",
        "logins": "Logins",
        "autofill": "Autofill",
        "all": "History",
    }
    db_type = db_types.get(data_type, "History")

    db_path, error = get_browser_db_path(browser, user_home, db_type=db_type)

    if not db_path:
        return jsonify(
            {"error": error or f"Không thể lấy đường dẫn cơ sở dữ liệu cho {browser}."}
        )

    if not db_path.exists():
        return jsonify(
            {
                "error": f"File cơ sở dữ liệu không tồn tại: {db_path}. Đảm bảo trình duyệt đã được cài đặt và có dữ liệu."
            }
        )

    data, error = read_browser_data(
        db_path, db_type, browser, limit, data_type, page=1, items_per_page=limit
    )
    if not data:
        return jsonify(
            {
                "error": error
                or f"Không thể trích xuất dữ liệu cho loại {data_type} trên {browser.capitalize()}."
            }
        )

    if "data" not in data or not data["data"]:
        return jsonify(
            {
                "error": f"Không tìm thấy dữ liệu cho loại {data_type} trên {browser.capitalize()} để tải xuống dưới dạng CSV."
            }
        )

    output_file = (
        f"browser_data_{browser}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    success, result = save_to_csv(data["data"], output_file)
    if success:
        return send_file(result, as_attachment=True, download_name=output_file)
    return jsonify({"error": result})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
