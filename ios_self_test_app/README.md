# Ứng Dụng Hướng Dẫn Tự Kiểm Tra Chức Năng iPhone (iOS Self-Test App)

Thư mục này chứa mã nguồn SwiftUI hoàn chỉnh cho ứng dụng chạy trực tiếp trên iPhone để tự động/hướng dẫn chẩn đoán các linh kiện phần cứng theo đúng kịch bản yêu cầu.

## Các chức năng ứng dụng thực hiện:
1. **Thông tin thiết bị (DEVICE_INFO):** Tự động truy vấn Model, iOS, Mức Pin, Trạng thái Sạc.
2. **Cảm biến chuyển động (SENSORS):** Đọc dữ liệu Gia tốc kế (Accelerometer) thời gian thực.
3. **Camera trước & sau (CAMERA):** Mở giao diện camera kiểm tra thấu kính, điểm đen.
4. **Âm thanh phát/thu (AUDIO):** Phát tone mẫu tần số cao kiểm tra loa ngoài & micro.
5. **Cảm ứng màn hình (TOUCHSCREEN):** Vẽ lưới ô vuông để vuốt toàn diện kiểm tra vùng chết cảm ứng.
6. **Màu sắc hiển thị (DISPLAY):** Chuyển màn hình thành các màu đơn sắc Red, Green, Blue, White, Black để tìm điểm chết LCD/OLED hoặc sọc màn hình.
7. **Cảm biến tiệm cận (PROXIMITY):** Đo cảm biến tắt màn hình khi áp tai / che Dynamic Island.
8. **Sinh trắc học (BIOMETRIC):** Kiểm tra khả năng mở khóa bằng Face ID / Touch ID.
9. **Gửi báo cáo:** Tự đóng gói thành JSON và thực hiện HTTP POST lên Ubuntu Server.

---

## Cách biên dịch và cài đặt (Bắt buộc dùng Xcode trên macOS):

1. **Chuẩn bị:**
   - Một máy tính Mac có cài **Xcode 15+**.
   - Cáp USB kết nối iPhone với máy Mac.

2. **Tạo Project mới:**
   - Mở Xcode -> **Create New Project** -> Chọn **App** dưới tab iOS -> Nhấn Next.
   - Đặt tên Project: `IPhoneSelfTest`.
   - Chọn Interface: **SwiftUI**, Language: **Swift**.
   - Nhấn Next và lưu project.

3. **Thay thế mã nguồn:**
   - Copy toàn bộ nội dung file [ContentView.swift](file:///home/rd/Downloads/iphone_activation_ui/ios_self_test_app/ContentView.swift) trong thư mục này.
   - Mở Xcode, click chọn file `ContentView.swift` trong danh sách file bên trái và dán đè toàn bộ code vừa copy vào.

4. **Cấu hình Quyền Truy Cập (Permissions):**
   - Click chọn file cấu hình Project chính (ở trên cùng danh sách bên trái).
   - Vào tab **Info** (hoặc mở file `Info.plist`).
   - Thêm các khóa sau cùng mô tả lý do cấp quyền (để camera/micro/cảm biến hoạt động):
     - `Privacy - Camera Usage Description` -> *Ứng dụng cần quyền Camera để chụp và test thấu kính.*
     - `Privacy - Microphone Usage Description` -> *Ứng dụng cần quyền Microphone để thu âm thanh tone kiểm tra.*
     - `Privacy - Local Network Usage Description` -> *Ứng dụng cần kết nối Local Network để gửi JSON báo cáo về máy Ubuntu.*

5. **Build & Ký ứng dụng (Signing):**
   - Vào tab **Signing & Capabilities** trong Xcode.
   - Tích chọn **Automatically manage signing**.
   - Chọn Team phát triển của bạn (Apple Developer Account miễn phí hoặc trả phí).
   - Chọn iPhone của bạn làm thiết bị mục tiêu (Target Device) ở thanh trên cùng.
   - Nhấn nút **Play / Run** (hoặc `Cmd + R`) để cài ứng dụng trực tiếp lên iPhone qua cáp.

6. **Trích xuất file `.ipa` (Để cài đặt tự động từ Tool Ubuntu):**
   - Trên Xcode, chọn thiết bị đích là `Any iOS Device (arm64)`.
   - Chọn Menu **Product** -> **Archive**.
   - Khi Archive xong, cửa sổ Organizer sẽ hiện ra -> Chọn **Distribute App** -> Chọn **Ad Hoc** hoặc **Development** -> Lưu file `.ipa` ra máy.
   - Copy file `.ipa` này sang máy chạy Ubuntu của bạn và cấu hình đường dẫn file trên giao diện tool để kích hoạt chế độ tự động cài đặt sau khi Active!
