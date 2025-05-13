# HƯỚNG DẪN SỬ DỤNG PROJECT: THU THẬP THÔNG TIN AN NINH MẠNG TỪ TRÌNH DUYỆT WEB

## MỤC LỤC
- [1. Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
- [2. Cấu trúc thư mục dự án](#2-cấu-trúc-thư-mục-dự-án)
- [3. Yêu cầu hệ thống và cài đặt](#3-yêu-cầu-hệ-thống-và-cài-đặt)
  - [3.1 Yêu cầu hệ thống](#31-yêu-cầu-hệ-thống)
  - [3.2 Cài đặt môi trường](#32-cài-đặt-môi-trường)
- [4. Hướng dẫn chạy ứng dụng](#4-hướng-dẫn-chạy-ứng-dụng)
  - [4.1 Chuẩn bị dữ liệu](#41-chuẩn-bị-dữ-liệu)
  - [4.2 Chạy ứng dụng](#42-chạy-ứng-dụng)
- [5. Hướng dẫn sử dụng ứng dụng](#5-hướng-dẫn-sử-dụng-ứng-dụng)
- [6. Lưu ý bảo mật và triển khai](#6-lưu-ý-bảo-mật-và-triển-khai)

---

## 1. Giới thiệu tổng quan

Project **"Thu thập thông tin an ninh mạng từ trình duyệt web"** là một ứng dụng Python sử dụng framework Flask, được thiết kế để thu thập và phân tích dữ liệu từ các trình duyệt web phổ biến như Brave, Microsoft Edge, và Mozilla Firefox. Ứng dụng cho phép người dùng truy xuất thông tin như lịch sử duyệt web, cookie, hoặc dữ liệu đăng nhập (nếu có) từ các trình duyệt, hiển thị kết quả trên giao diện web đơn giản.

**Mục tiêu chính của project:**
- Hỗ trợ nghiên cứu và phân tích thông tin an ninh mạng từ trình duyệt.
- Minh họa các kỹ thuật thu thập dữ liệu từ trình duyệt.
- Nâng cao nhận thức về bảo mật và quyền riêng tư khi sử dụng trình duyệt.

---

## 2. Cấu trúc thư mục dự án

Cấu trúc thư mục của project được tổ chức như sau:

```
TPIT
├── static/
│   ├── script.js        # File JavaScript xử lý giao diện web
│   └── styles.css       # File CSS định dạng giao diện web
├── templates/
│   └── index.html       # Giao diện web chính của ứng dụng
├── app.py               # File chính chạy ứng dụng Flask
├── brave_reader.py      # Module thu thập dữ liệu từ trình duyệt Brave
├── edge_reader.py       # Module thu thập dữ liệu từ trình duyệt Edge
├── firefox_reader.py    # Module thu thập dữ liệu từ trình duyệt Firefox
├── Readme.md            # File mô tả tổng quan project (file này)
└── requirements.txt     # File liệt kê các thư viện Python cần thiết
```

---

## 3. Yêu cầu hệ thống và cài đặt

### 3.1 Yêu cầu hệ thống

Để chạy project, hệ thống cần đáp ứng các yêu cầu sau:
- **Hệ điều hành**: Windows, macOS, hoặc Linux.
- **Python**: Phiên bản 3.8 trở lên.
- **Trình duyệt**: Đã cài đặt ít nhất một trong các trình duyệt Brave, Microsoft Edge, hoặc Mozilla Firefox.
- **Truy cập Internet**: Để tải các thư viện Python nếu cần.

### 3.2 Cài đặt môi trường

Thực hiện các bước sau để cài đặt môi trường và chuẩn bị chạy ứng dụng:

**Bước 1: Cài đặt Python**
- Tải và cài đặt Python từ trang chủ: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- Kiểm tra phiên bản Python:
  ```bash
  python --version
  ```
  Đảm bảo phiên bản Python >= 3.8.

**Bước 2: Tải mã nguồn project**
- Sao chép thư mục project (`TPIT`) vào máy tính của bạn.
- Ví dụ: Đặt thư mục tại `C:\Projects\TPIT` (Windows) hoặc `/home/user/TPIT` (Linux/macOS).

**Bước 3: Tạo môi trường ảo (khuyến nghị)**
- Mở terminal/command prompt, di chuyển đến thư mục project:
  ```bash
  cd C:\Projects\TPIT
  ```
- Tạo môi trường ảo:
  ```bash
  python -m venv venv
  ```
- Kích hoạt môi trường ảo:
  - Windows:
    ```bash
    venv\Scripts\activate
    ```
  - Linux/macOS:
    ```bash
    source venv/bin/activate
    ```

**Bước 4: Cài đặt các thư viện cần thiết**
- Trong môi trường ảo, cài đặt các thư viện từ file `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```
- File `requirements.txt` thường bao gồm các thư viện như:
  ```
  flask
  sqlite3  # Thường có sẵn trong Python
  ```
- Nếu thiếu thư viện, bổ sung bằng lệnh:
  ```bash
  pip install <tên_thư_viện>
  ```

---

## 4. Hướng dẫn chạy ứng dụng

### 4.1 Chuẩn bị dữ liệu

- Đảm bảo các trình duyệt Brave, Edge, hoặc Firefox đã được cài đặt và có dữ liệu (lịch sử duyệt web, cookie, v.v.).
- Các file dữ liệu trình duyệt thường nằm ở:
  - **Brave**: `C:\Users\<Username>\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default`
  - **Edge**: `C:\Users\<Username>\AppData\Local\Microsoft\Edge\User Data\Default`
  - **Firefox**: `C:\Users\<Username>\AppData\Roaming\Mozilla\Firefox\Profiles\<profile_name>`

### 4.2 Chạy ứng dụng

- Trong terminal, đảm bảo môi trường ảo đã được kích hoạt (xem Bước 3.2).
- Chạy file `app.py`:
  ```bash
  python app.py
  ```
- Ứng dụng Flask sẽ khởi động, hiển thị thông báo tương tự:
  ```
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
  ```
- Mở trình duyệt bất kỳ, truy cập địa chỉ:
  ```
  http://127.0.0.1:5000/
  ```
- Giao diện web sẽ hiển thị, cho phép bạn chọn trình duyệt và xem dữ liệu thu thập được.

---

## 5. Hướng dẫn sử dụng ứng dụng

- Khi truy cập `http://127.0.0.1:5000/`, giao diện web chính (`index.html`) sẽ hiển thị.
- Giao diện bao gồm:
  - Một dropdown menu để chọn trình duyệt (Brave, Edge, Firefox).
  - Nút "Thu thập dữ liệu" để chạy các module (`brave_reader.py`, `edge_reader.py`, `firefox_reader.py`).
  - Khu vực hiển thị kết quả (lịch sử duyệt web, cookie, v.v.).
- **Cách sử dụng**:
  1. Chọn trình duyệt từ dropdown menu.
  2. Nhấn nút "Thu thập dữ liệu".
  3. Kết quả sẽ hiển thị trên giao diện (ví dụ: danh sách URL đã truy cập, cookie phiên làm việc).
- File `script.js` xử lý tương tác giao diện, `styles.css` định dạng giao diện.

---

## 6. Lưu ý bảo mật và triển khai

- **Bảo mật**:
  - Ứng dụng truy cập dữ liệu nhạy cảm từ trình duyệt (lịch sử, cookie). Không chia sẻ ứng dụng với người không tin cậy.
  - Chỉ chạy ứng dụng trên máy tính cá nhân, không triển khai trên máy chủ công khai nếu chưa có biện pháp bảo mật (HTTPS, xác thực người dùng).
  - Xóa dữ liệu thu thập sau khi sử dụng để tránh rò rỉ thông tin.
- **Triển khai**:
  - Nếu muốn triển khai trên máy chủ, sử dụng WSGI server như Gunicorn và proxy như Nginx.
  - Ví dụ:
    ```bash
    gunicorn --bind 0.0.0.0:5000 app:app
    ```
  - Đảm bảo cấu hình tường lửa và chỉ cho phép truy cập từ địa chỉ IP tin cậy.
- **Hạn chế**:
  - Ứng dụng không hỗ trợ tất cả các trình duyệt (chỉ Brave, Edge, Firefox).
  - Một số dữ liệu trình duyệt có thể bị mã hóa (như mật khẩu), cần thêm module giải mã nếu muốn truy xuất.

---

**HẾT**