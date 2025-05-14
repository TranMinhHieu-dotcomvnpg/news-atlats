# Hướng dẫn cài đặt và chạy dự án web
## Các bước cài đặt

### 1. Clone repository (nếu sử dụng Git)
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Tạo và kích hoạt môi trường ảo (Virtual Environment)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### 4. Cấu hình cơ sở dữ liệu
- Mở file `settings.py` trong thư mục `config`
- Cập nhật các thông tin cấu hình cơ sở dữ liệu nếu cần thiết

### 5. Chạy migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
### 6. Chạy server
```bash
python manage.py runserver
```

### 7. Truy cập website
- Mở trình duyệt web và truy cập: `http://127.0.0.1:8000`
- Đăng nhập với tài khoản superuser đã tạo ở bước 6

## Xử lý lỗi thường gặp
1. Nếu gặp lỗi "ModuleNotFoundError":
   - Kiểm tra môi trường ảo đã được kích hoạt chưa
   - Chạy lại lệnh `pip install -r requirements.txt`

2. Nếu gặp lỗi database:
   - Kiểm tra cấu hình database trong `settings.py`
   - Chạy lại các lệnh migration

3. Nếu gặp lỗi static files:
   - Chạy lệnh `python manage.py collectstatic`
