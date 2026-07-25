import subprocess
from dataclasses import dataclass
from .command import run_command

@dataclass
class AndroidDeviceInfo:
    serial: str
    model: str = "Android"
    brand: str = "Không rõ"
    android_version: str = "Không rõ"
    imei: str = "Không rõ"

def run_adb(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess | None:
    try:
        # Run local adb command
        cmd = ["adb"] + args
        result = run_command(cmd, timeout=timeout, check=False)
        return result
    except Exception:
        return None

def check_adb_installed() -> bool:
    try:
        import shutil
        return shutil.which("adb") is not None
    except Exception:
        return False

def discover_android_devices() -> list[AndroidDeviceInfo]:
    devices: list[AndroidDeviceInfo] = []
    if not check_adb_installed():
        return devices

    res = run_adb(["devices"])
    if not res or res.returncode != 0:
        return devices

    lines = res.stdout.splitlines()
    serials = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2 and parts[1] == "device":
            serials.append(parts[0])

    for serial in serials:
        model = "Android Device"
        brand = "Không rõ"
        version = "Không rõ"
        imei = "Không rõ"

        # Fetch model
        m_res = run_adb(["-s", serial, "shell", "getprop", "ro.product.model"])
        if m_res and m_res.returncode == 0:
            model = m_res.stdout.strip() or model

        # Fetch brand
        b_res = run_adb(["-s", serial, "shell", "getprop", "ro.product.brand"])
        if b_res and b_res.returncode == 0:
            brand = b_res.stdout.strip().capitalize() or brand

        # Fetch android version
        v_res = run_adb(["-s", serial, "shell", "getprop", "ro.build.version.release"])
        if v_res and v_res.returncode == 0:
            version = v_res.stdout.strip() or version

        # Try to fetch IMEI (Requires specific permissions or service calls, fallback to unknown)
        # We can try a simple service call to iphonesubinfo but it is version dependent
        devices.append(AndroidDeviceInfo(
            serial=serial,
            model=model,
            brand=brand,
            android_version=version,
            imei=imei
        ))

    return devices

def bypass_android_setup(serial: str) -> tuple[bool, str]:
    import json
    output_log = []
    
    # 1. Try Trade-in Mode (Android 16+) first
    output_log.append("Đang kiểm tra hỗ trợ Android 16 Trade-in Mode...")
    t_status = run_adb(["-s", serial, "shell", "tradeinmode", "wait-until-ready", "getstatus"])
    
    trade_in_supported = False
    frp_locked = False
    
    if t_status and t_status.returncode == 0:
        stdout_clean = t_status.stdout.strip()
        try:
            status_data = json.loads(stdout_clean)
            output_log.append(f"Trạng thái Trade-in Mode: {stdout_clean}")
            trade_in_supported = True
            
            # Check for FRP lock status
            locks = status_data.get("locks", {})
            if isinstance(locks, dict):
                frp_locked = locks.get("factory_reset_protection", False)
            else:
                frp_locked = False
                
            if frp_locked:
                output_log.append("Cảnh báo: Thiết bị bị khóa FRP (Factory Reset Protection)! Không thể dùng Trade-in Mode.")
        except Exception as e:
            output_log.append(f"Không thể parse JSON trạng thái Trade-in Mode: {e}")
            if "factory_reset_protection" in stdout_clean.lower():
                trade_in_supported = True
                if '"factory_reset_protection": true' in stdout_clean.replace(" ", "").lower():
                    frp_locked = True
                    output_log.append("Cảnh báo: Phát hiện thiết bị bị khóa FRP qua chuỗi text.")
            
    if trade_in_supported and not frp_locked:
        output_log.append("Thiết bị hỗ trợ Trade-in Mode. Bắt đầu chạy evaluate...")
        t_eval = run_adb(["-s", serial, "shell", "tradeinmode", "wait-until-ready", "evaluate"])
        if t_eval:
            output_log.append(f"tradeinmode evaluate: {t_eval.combined.strip()}")
            if t_eval.returncode == 0 and "error" not in t_eval.combined.lower():
                output_log.append("Kích hoạt Trade-in Mode thành công! Chờ 3 giây để thiết lập hoàn tất...")
                import time
                time.sleep(3)
                
                # Check provisioned & setup complete states for verification logging
                p_res = run_adb(["-s", serial, "shell", "settings", "get", "global", "device_provisioned"])
                u_res = run_adb(["-s", serial, "shell", "settings", "get", "secure", "user_setup_complete"])
                
                p_val = p_res.stdout.strip() if p_res else ""
                u_val = u_res.stdout.strip() if u_res else ""
                output_log.append(f"device_provisioned = {p_val}")
                output_log.append(f"user_setup_complete = {u_val}")
                
                combined_log = "\n".join(output_log)
                return (True, f"Kích hoạt Android 16 Trade-in Mode thành công!\n{combined_log}")
            else:
                output_log.append("Lỗi khi chạy lệnh tradeinmode evaluate.")
        else:
            output_log.append("Không nhận được phản hồi từ lệnh tradeinmode evaluate.")
            
    # 2. Fallback to legacy settings put method
    output_log.append("Chuyển sang phương án dự phòng (Legacy Setup Bypass)...")
    
    p_res = run_adb(["-s", serial, "shell", "settings", "put", "global", "device_provisioned", "1"])
    u_res = run_adb(["-s", serial, "shell", "settings", "put", "secure", "user_setup_complete", "1"])
    
    p_ok = p_res and p_res.returncode == 0 and "error" not in p_res.combined.lower()
    u_ok = u_res and u_res.returncode == 0 and "error" not in u_res.combined.lower()
    
    if p_res:
        output_log.append(f"device_provisioned: {p_res.combined.strip()}")
    else:
        output_log.append("device_provisioned: Không có phản hồi từ ADB")
        
    if u_res:
        output_log.append(f"user_setup_complete: {u_res.combined.strip()}")
    else:
        output_log.append("user_setup_complete: Không có phản hồi từ ADB")

    # Try disabling common setup wizard packages
    wizards = [
        "com.google.android.setupwizard",
        "com.sec.android.app.setupwizard",  # Samsung
        "com.miui.setupwizard",            # Xiaomi
        "com.coloros.setupwizard",          # Oppo/Realme
        "com.huawei.android.setupwizard",   # Huawei
        "com.vivo.setupwizard",             # Vivo
    ]
    
    disabled_any = False
    for wizard in wizards:
        dis_res = run_adb(["-s", serial, "shell", "pm", "disable-user", wizard])
        if dis_res and dis_res.returncode == 0 and "error" not in dis_res.combined.lower():
            disabled_any = True
            output_log.append(f"Tắt thành công: {wizard}")
            
    combined_log = "\n".join(output_log)
    
    if not p_ok or not u_ok:
        # Check if the device is unauthorized
        dev_res = run_command(["adb", "devices"], timeout=10, check=False)
        is_unauthorized = False
        if dev_res:
            for line in dev_res.stdout.splitlines():
                if serial in line and "unauthorized" in line:
                    is_unauthorized = True
                    break
        
        if is_unauthorized:
            return (False, f"Thiết bị chưa được ủy quyền (unauthorized)!\nVui lòng nhấn 'Cho phép gỡ lỗi USB' (Allow USB Debugging) trên màn hình điện thoại rồi thử lại.\n{combined_log}")
        return (False, f"Lỗi kích hoạt (lệnh settings put thất bại hoặc lỗi kết nối):\n{combined_log}")
        
    return (True, f"Kích hoạt thành công (Legacy)!\n{combined_log}")


def install_apk(serial: str, apk_path: str) -> tuple[bool, str]:
    res = run_adb(["-s", serial, "install", "-r", apk_path])
    if res and res.returncode == 0 and "error" not in res.combined.lower():
        return (True, "Cài đặt ứng dụng test (.apk) thành công!")
    return (False, f"Cài đặt thất bại:\n{res.combined if res else 'Không kết nối được adb'}")

def erase_android(serial: str) -> tuple[bool, str]:
    # Standard factory reset command via ADB: reboot to recovery and perform factory reset, or send recovery command
    # adb reboot recovery is the most standard without root
    res = run_adb(["-s", serial, "reboot", "recovery"])
    if res and res.returncode == 0 and "error" not in res.combined.lower():
        return (True, "Đã gửi lệnh khởi động vào Chế độ khôi phục (Recovery). Thiết bị sẽ tự động reset.")
    return (False, f"Gửi lệnh Erase thất bại:\n{res.combined if res else 'Không kết nối được adb'}")

def send_at_cmd(ser, cmd: str, timeout: float = 1.5) -> str:
    import time
    ser.reset_input_buffer()
    ser.write(f"{cmd}\r\n".encode())
    
    start_time = time.time()
    response = ""
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            response += chunk
            if "OK" in response or "ERROR" in response:
                break
        time.sleep(0.05)
    return response

def enable_samsung_adb() -> tuple[bool, str]:
    import time
    try:
        import serial
        import serial.tools.list_ports
    except ImportError:
        return (False, "Thư viện pyserial chưa được cài đặt. Vui lòng cài đặt bằng: pip install pyserial")

    ports = []
    for port in serial.tools.list_ports.comports():
        desc = (port.description or "").lower()
        mfg = (port.manufacturer or "").lower()
        if "samsung" in desc or "samsung" in mfg or "acm" in port.device.lower() or "usb" in port.device.lower():
            ports.append(port.device)
            
    if not ports:
        import glob
        ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
        
    ports = sorted(list(set(ports)))
    if not ports:
        return (False, "Không tìm thấy cổng serial/modem nào của điện thoại. Hãy chắc chắn máy đã cắm cáp và ở màn hình Test Mode (*#0*#).")

    logs = []
    success = False
    
    # AT command sequence to enable ADB via Test Mode
    commands = [
        "AT",
        "AT+SWATD=0",
        "AT+ACTIVATE=0,0,0",
        "AT+SWATD=1",
        "AT+KSTRINGB=0,3",
        "AT+DUMPCTRL=1,0",
        "AT+DEBUGLVC=0,5"
    ]
    
    for port in ports:
        logs.append(f"Thử cổng: {port}")
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1.0, write_timeout=1.0)
        except Exception as e:
            logs.append(f"Không thể mở cổng {port}: {e}")
            continue
            
        try:
            # Explicitly toggle DTR and RTS which is required for some USB modems to transmit data
            ser.dtr = True
            ser.rts = True
            time.sleep(0.2)
            
            # Send initial AT command to wake up the port / detect baudrate
            resp = ""
            for retry in range(3):
                resp = send_at_cmd(ser, "AT", timeout=1.0)
                if "OK" in resp:
                    break
                time.sleep(0.1)
                
            if "OK" not in resp:
                logs.append(f"Cổng {port} không phản hồi OK với lệnh AT (Nhận được: {resp.strip()})")
                ser.close()
                continue
                
            logs.append(f"Phát hiện modem phản hồi tại {port}. Bắt đầu gửi chuỗi lệnh kích hoạt ADB...")
            
            for cmd in commands[1:]:
                resp = send_at_cmd(ser, cmd, timeout=1.5)
                clean_resp = resp.strip().replace('\r', ' ').replace('\n', ' ')
                logs.append(f"Gửi: {cmd} -> Nhận: {clean_resp}")
                
            success = True
            ser.close()
            break
        except Exception as e:
            logs.append(f"Lỗi khi truyền dữ liệu qua {port}: {e}")
            try:
                ser.close()
            except Exception:
                pass

    log_str = "\n".join(logs)
    if success:
        return (True, f"Đã gửi lệnh kích hoạt ADB thành công qua cổng serial.\nVui lòng xem trên màn hình điện thoại và nhấn 'Cho phép gỡ lỗi USB'!\n\nChi tiết phản hồi:\n{log_str}")
    else:
        return (False, f"Không thể kích hoạt ADB qua cổng serial.\nHãy đảm bảo điện thoại đã được mở màn hình Test Mode (*#0*#) bằng cách vào Cuộc gọi khẩn cấp.\n\nNhật ký thử nghiệm:\n{log_str}")
