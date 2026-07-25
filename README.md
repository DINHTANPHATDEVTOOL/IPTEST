# Trạm Kích Hoạt & Chẩn Đoán Thiết Bị Đa Nền Tảng (iOS & Android)

Trạm chẩn đoán và tự động hóa kích hoạt di động tích hợp giao diện người dùng trực quan trên Ubuntu. Bản cập nhật này hỗ trợ song song hai tab làm việc cho cả thiết bị Apple iOS và Google Android.

---

## 🚀 Các Tính Năng Chính

### 1. Tab iOS Workstation
- **Tự động quét cổng USB**: Phát hiện nhanh một hoặc nhiều iPhone đang kết nối.
- **Thông tin thiết bị**: Hiển thị Device Name, ProductType, phiên bản iOS, kiểu kết nối, UDID và trạng thái kích hoạt hiện tại.
- **Kích hoạt nhanh**: Chạy kích hoạt tự động (`ideviceactivation`) cho thiết bị đã chọn.
- **Khôi phục cài đặt gốc**: Hỗ trợ Erase nhanh qua `pymobiledevice3` để đưa máy về trạng thái Hello sau khi hoàn tất kiểm tra.
- **Cơ chế chẩn đoán API**: Tích hợp FastAPI nhận kết quả kiểm tra phần cứng (màn hình, camera, loa, mic...) từ ứng dụng Web chẩn đoán chạy trên iPhone.

### 2. Tab Android Workstation
- **Tự động dò tìm**: Quét thiết bị Android kết nối qua USB bằng ADB, tự động lấy thông tin Model, Hãng sản xuất, Phiên bản Android và Serial.
- **Kích hoạt Android 16+ Trade-in Mode (Phương án ưu tiên)**:
  - Tự động kiểm tra tính khả dụng của lệnh `tradeinmode`.
  - Kiểm tra trạng thái khóa chống trộm (FRP) của máy: Chỉ kích hoạt nếu thiết bị không có FRP (`"factory_reset_protection": false`).
  - Gửi lệnh `evaluate` để tự động bỏ qua Setup Wizard, đưa máy vào Home và kích hoạt đầy đủ ADB để chẩn đoán.
- **Cơ chế dự phòng (Legacy Setup Bypass)**:
  - Nếu máy chạy Android đời cũ (< 16), tự động chuyển sang cơ chế ghi đè biến hệ thống `device_provisioned` & `user_setup_complete`.
  - Tự động đóng/vô hiệu hóa các trình hướng dẫn cài đặt Setup Wizard của các hãng lớn (Google, Samsung, Xiaomi, Oppo, Vivo, Huawei).
- **Tự động khôi phục kết nối (ADB Reconnect)**:
  - Tự động chạy lệnh `adb reconnect` trước mỗi lần quét thiết bị để khắc phục triệt để tình trạng kết nối USB chập chờn hoặc máy rơi vào trạng thái ngoại tuyến (offline).
- **Samsung ADB Serial Enabler (*#0*#)**:
  - Dành cho các thiết bị Samsung cần kích hoạt ADB thủ công thông qua cổng modem Serial/COM (khi thiết bị đang ở màn hình Test Mode `*#0*#`).
- **Cài đặt App Test**: Tự động cài đặt tệp ứng dụng kiểm tra `.apk` chỉ với 1 click.
- **Erase/Reset**: Gửi lệnh đưa thiết bị vào chế độ Recovery để khôi phục cài đặt gốc.

---

## 📦 Yêu Cầu Hệ Thống & Cài Đặt

Mở terminal trong thư mục dự án và chạy tệp cài đặt tự động:

```bash
chmod +x install.sh
./install.sh
```

Tệp script sẽ tự động cấu hình Virtual Environment Python (`.venv`), cập nhật các thư viện bổ sung (bao gồm `pyserial`, `pymobiledevice3`) và cài đặt các dependencies hệ thống.

---

## ⚙️ Hướng Dẫn Sử Dụng

### Khởi chạy phần mềm:
```bash
./run.sh
```

### Quy trình kích hoạt Android:
1. Đảm bảo điện thoại Android đã bật chế độ Gỡ lỗi USB (USB Debugging) hoặc chạy phiên bản Android 16+ đang ở Setup Wizard (chưa cấu hình Wi-Fi, không lắp SIM, không khóa FRP).
2. Kết nối điện thoại với máy tính qua cáp USB.
3. Chờ thiết bị xuất hiện trong bảng danh sách Android (hoặc bấm **Quét lại Android** để làm mới cổng).
4. Nhấn **Active Android**. Phần mềm sẽ tự động dò tìm phiên bản hệ điều hành và thực thi phương pháp kích hoạt tương thích nhất.
5. Khi hoàn tất, bạn có thể thiết lập đường dẫn tệp ứng dụng chẩn đoán `.apk` và nhấn **Cài App Test (.apk)** để bắt đầu kiểm tra thiết bị.
