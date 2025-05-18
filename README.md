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
- hoặc có thể giữ nguyên và sử dụng 

### 5.1 Chạy server
```bash
python manage.py runserver 8080
```

### 6.1 Truy cập website
- Mở trình duyệt web và truy cập: `http://127.0.0.1:8080`
- để có thể cập nhật các bài báo mới và lưu vào mongo atlats dùng lệnh: docker-compose up -d zookeeper kafka
- để cập nhật lại kho lưu trữ tìm kiếm tin tức bằng elasticsearch, dùng lệnh: python Elastic_Search/mongo_to_es.py để cập nhật lại kho tìm kiếm
- 
### 5.2 Nếu người dùng muốn chạy localhost
- docker-compose up --build   : mục đích tạo các container trong docker để thực hiện chạy localhost
- docker-compose up -d    : nếu sau khi đã tạo thành công có thể tái khởi động bằng lệnh này
### 6.2 Truy cập web
- truy cập thông qua localhost:/8080
- hoặc khi chạy lệnh: " docker-compose up -d ": thì vào docker tìm container: " news_atlats_ai-web-1 " . và truy cập localhost
## Xử lý lỗi thường gặp
1. Nếu gặp lỗi "ModuleNotFoundError":
   - Kiểm tra môi trường ảo đã được kích hoạt chưa
   - Chạy lại lệnh `pip install -r requirements.txt`

2. Nếu gặp lỗi database:
   - Kiểm tra cấu hình database trong `settings.py`
   - Chạy lại các lệnh migration

3. Nếu gặp lỗi static files:
   - Chạy lệnh `python manage.py collectstatic`
