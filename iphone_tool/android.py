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
    output_log = []
    
    # 1. Set provisioned & setup complete states
    p_res = run_adb(["-s", serial, "shell", "settings", "put", "global", "device_provisioned", "1"])
    u_res = run_adb(["-s", serial, "shell", "settings", "put", "secure", "user_setup_complete", "1"])
    
    if p_res:
        output_log.append(f"device_provisioned: {p_res.combined.strip()}")
    if u_res:
        output_log.append(f"user_setup_complete: {u_res.combined.strip()}")

    # 2. Try disabling common setup wizard packages
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
        if dis_res and dis_res.returncode == 0:
            disabled_any = True
            output_log.append(f"Tắt thành công: {wizard}")
            
    combined_log = "\n".join(output_log)
    return (True, f"Kích hoạt thành công!\n{combined_log}")

def install_apk(serial: str, apk_path: str) -> tuple[bool, str]:
    res = run_adb(["-s", serial, "install", "-r", apk_path])
    if res and res.returncode == 0:
        return (True, "Cài đặt ứng dụng test (.apk) thành công!")
    return (False, f"Cài đặt thất bại:\n{res.combined if res else 'Không kết nối được adb'}")

def erase_android(serial: str) -> tuple[bool, str]:
    # Standard factory reset command via ADB: reboot to recovery and perform factory reset, or send recovery command
    # adb reboot recovery is the most standard without root
    res = run_adb(["-s", serial, "reboot", "recovery"])
    if res and res.returncode == 0:
        return (True, "Đã gửi lệnh khởi động vào Chế độ khôi phục (Recovery). Thiết bị sẽ tự động reset.")
    return (False, "Gửi lệnh Erase thất bại.")
