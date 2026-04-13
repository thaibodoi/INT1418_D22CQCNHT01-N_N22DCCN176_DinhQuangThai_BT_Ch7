# RS-Tree Surveillance Desktop Application

Đây là một ứng dụng Desktop (không phải Web) được viết bằng **Python** để thiết kế và triển khai cấu trúc dữ liệu **RS-tree** quản lý video đa phương tiện.

## 1. Tính năng chính
- Xây dựng RS-tree dựa trên phân đoạn thời gian (Segment Table).
- Hỗ trợ 8 hàm truy vấn dữ liệu từ đối tượng đến hoạt động và thuộc tính.
- Giao diện Dashboard 4 camera hiện đại với Dark Mode.
- Điều khiển Timeline đồng bộ để xem dữ liệu theo frame.

## 2. Cấu trúc thư mục
- `main_app.py`: Điểm nhập chính của ứng dụng GUI.
- `rs_tree_lib/`: Thư viện lõi chứa logic RS-tree và OBJECTARRAY.
- `data.json`: Bảng dữ liệu phân đoạn mẫu cho 4 camera khu phố.

## 3. Cách chạy ứng dụng
1. Đảm bảo đã cài đặt Python 3.8+.
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install customtkinter pillow
   ```
3. Khởi chạy ứng dụng:
   ```bash
   python main_app.py
   ```

## 4. Các truy vấn hỗ trợ
Hệ thống cho phép thực hiện 8 loại truy vấn (từ i đến viii) như yêu cầu trong sách giáo khoa của V.S. Subrahmanian.
