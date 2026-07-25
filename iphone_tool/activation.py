from __future__ import annotations
import re
from dataclasses import dataclass
from enum import Enum
from .command import run_command

class ActivationStatus(str, Enum):
    ACTIVATED = "activated"
    UNACTIVATED = "unactivated"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

@dataclass
class ActivationResult:
    udid: str
    status: ActivationStatus
    message: str
    raw_output: str = ""

BLOCK_PATTERNS = ("activation lock", "apple id", "apple account", "owner", "remote management", "sim required")

def list_udids() -> list[str]:
    result = run_command(["idevice_id", "-l"], timeout=15, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]

def get_activation_state(udid: str, timeout: int = 30) -> ActivationResult:
    result = run_command(["ideviceactivation", "state", "-u", udid], timeout=timeout, check=False)
    output, lower = result.combined, result.combined.lower()
    
    use_fallback = False
    if "error" in lower or "failed" in lower or result.returncode != 0 or not output.strip():
        use_fallback = True
        
    if use_fallback:
        py_res = run_command(["pymobiledevice3", "activation", "state", "--udid", udid], timeout=timeout, check=False)
        if py_res.returncode != 0:
            py_res = run_command(["pymobiledevice3", "activation", "state", "--udid", udid, "--userspace"], timeout=timeout, check=False)
        if py_res.returncode == 0:
            output = py_res.combined
            lower = py_res.combined.lower()
            
    if any(p in lower for p in BLOCK_PATTERNS):
        return ActivationResult(udid, ActivationStatus.BLOCKED, "Thiết bị yêu cầu thông tin chủ sở hữu hoặc điều kiện kích hoạt.", output)
    if re.search(r"\bactivated\b", lower) and "unactivated" not in lower:
        return ActivationResult(udid, ActivationStatus.ACTIVATED, "Thiết bị đã được kích hoạt.", output)
    if any(x in lower for x in ("unactivated", "not activated", "inactive")):
        return ActivationResult(udid, ActivationStatus.UNACTIVATED, "Thiết bị chưa được kích hoạt.", output)
    return ActivationResult(udid, ActivationStatus.UNKNOWN, "Không xác định được trạng thái kích hoạt.", output)

def activate(udid: str, timeout: int = 120) -> ActivationResult:
    # 1. Thử lệnh kích hoạt truyền thống ideviceactivation
    result = run_command(["ideviceactivation", "activate", "-u", udid, "-b"], timeout=timeout, check=False)
    output = result.combined
    
    # 2. Nếu thất bại, thử lệnh kích hoạt hiện đại bằng pymobiledevice3 (tương thích iOS 17/18)
    if result.returncode != 0:
        py_res = run_command(["pymobiledevice3", "activation", "activate", "--udid", udid], timeout=timeout, check=False)
        output += "\n--- Phản hồi pymobiledevice3 ---\n" + py_res.combined
        if py_res.returncode != 0:
            py_res = run_command(["pymobiledevice3", "activation", "activate", "--udid", udid, "--userspace"], timeout=timeout, check=False)
            output += "\n--- Phản hồi pymobiledevice3 (userspace) ---\n" + py_res.combined
            result = py_res
        else:
            result = py_res

    lower = output.lower()
    if any(p in lower for p in BLOCK_PATTERNS):
        return ActivationResult(udid, ActivationStatus.BLOCKED, "Dừng: thiết bị cần thông tin chủ sở hữu/Activation Lock/SIM/MDM.", output)
        
    state = get_activation_state(udid, timeout=30)
    if state.status == ActivationStatus.ACTIVATED:
        state.message = "Kích hoạt thành công qua Apple activation service."
        state.raw_output = output + "\n" + state.raw_output

        # Thử cấu hình bỏ qua màn hình Hello bằng cách đặt Ngôn ngữ & Vùng và Giám sát thiết bị (supervise)
        try:
            # 1. Cài đặt ngôn ngữ (en) và vùng (en_US) để bỏ qua màn hình chọn Ngôn ngữ & Vùng
            lang_res = run_command(["pymobiledevice3", "lockdown", "language", "en", "--udid", udid], timeout=15, check=False)
            if lang_res.returncode != 0:
                run_command(["pymobiledevice3", "lockdown", "language", "en", "--udid", udid, "--userspace"], timeout=15, check=False)

            locale_res = run_command(["pymobiledevice3", "lockdown", "locale", "en_US", "--udid", udid], timeout=15, check=False)
            if locale_res.returncode != 0:
                run_command(["pymobiledevice3", "lockdown", "locale", "en_US", "--udid", udid, "--userspace"], timeout=15, check=False)

            # 2. Thực hiện giám sát thiết bị (supervise)
            supervise_result = run_command(
                ["pymobiledevice3", "profile", "supervise", "iPhone", "--udid", udid],
                timeout=60,
                check=False
            )
            # Thử lại với --userspace nếu chạy bình thường không thành công (dành cho iOS 17+)
            if supervise_result.returncode != 0:
                supervise_result = run_command(
                    ["pymobiledevice3", "profile", "supervise", "iPhone", "--udid", udid, "--userspace"],
                    timeout=60,
                    check=False
                )

            state.raw_output += f"\n--- Kết quả bỏ qua màn hình Hello (supervise) ---\n{supervise_result.combined}"
            if supervise_result.returncode == 0:
                state.message = "Kích hoạt và bỏ qua màn hình Hello thành công!"
            else:
                state.message = "Đã kích hoạt nhưng không thể tự động bỏ qua màn hình Hello. Vui lòng thao tác thủ công."
        except Exception as e:
            state.message = "Đã kích hoạt nhưng lỗi khi tự động bỏ qua màn hình Hello."
            state.raw_output += f"\nLỗi bỏ qua màn hình Hello: {e}"

        return state
        
    if result.returncode != 0:
        return ActivationResult(udid, state.status, f"Kích hoạt không thành công, mã lỗi {result.returncode}.", output)
    return state
