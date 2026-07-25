# iPhone Activation Tool — Ubuntu UI

Bản này **không dùng camera**. Tool mặc định xem iPhone đang ở màn hình **Hello**.

## Chức năng

- Tự quét một hoặc nhiều iPhone đang cắm USB.
- Hiển thị Device Name, ProductType, iOS, kiểu kết nối, UDID và trạng thái activation.
- Nút **Active iPhone** chạy `ideviceactivation` với đúng UDID đang chọn.
- Nút **Erase về cài đặt gốc** chỉ mở sau khi trạng thái là `Activated`.
- Trước khi xóa, người dùng phải xác nhận hai lần và nhập `ERASE`.
- Có nhật ký chi tiết ngay trên giao diện.

## Cài đặt

```bash
unzip iphone_activation_ui.zip
cd iphone_activation_ui
chmod +x install.sh
./install.sh
```

## Chạy

```bash
./run.sh
```

## Quy trình sử dụng

1. Cắm iPhone đang ở màn hình Hello.
2. Chờ thiết bị xuất hiện trong danh sách.
3. Chọn đúng UDID.
4. Nhấn **Active iPhone**.
5. Khi trạng thái chuyển thành **Đã kích hoạt**, nút **Erase về cài đặt gốc** sẽ được bật.
6. Khi cần xóa, nhấn Erase, xác nhận và nhập `ERASE`.

## Lệnh được sử dụng

```bash
idevice_id -l
ideviceactivation state -u UDID
ideviceactivation activate -u UDID -b
pymobiledevice3 backup2 erase-device --udid UDID
```

## Lưu ý

- Tool không vượt Activation Lock, Apple Account của chủ sở hữu, SIM lock hoặc MDM.
- Erase xóa toàn bộ dữ liệu và không thể hoàn tác.
- Nếu `pymobiledevice3 backup2 erase-device` thay đổi cú pháp ở phiên bản bạn cài, chạy:

```bash
pymobiledevice3 backup2 erase-device --help
```
