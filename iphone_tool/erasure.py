from __future__ import annotations

from dataclasses import dataclass

from .activation import ActivationStatus, get_activation_state, list_udids
from .command import run_command


@dataclass
class EraseResult:
    success: bool
    message: str
    raw_output: str = ""


def erase_device(udid: str, timeout: int = 180) -> EraseResult:
    state = get_activation_state(udid, timeout=30)
    if state.status != ActivationStatus.ACTIVATED:
        return EraseResult(False, "Chỉ được xóa khi iPhone đang ở trạng thái Activated.", state.raw_output)

    result = run_command(
        ["pymobiledevice3", "profile", "erase-device", "--udid", udid],
        timeout=timeout,
        check=False,
    )
    # Thử lại với --userspace nếu thất bại (dành cho iOS 17+)
    if result.returncode != 0:
        result = run_command(
            ["pymobiledevice3", "profile", "erase-device", "--udid", udid, "--userspace"],
            timeout=timeout,
            check=False,
        )
    output = result.combined
    lower = output.lower()

    success_markers = (
        "erase device",
        "erasing",
        "erase request",
        "success",
        "device disconnected",
    )
    if result.returncode == 0 or any(marker in lower for marker in success_markers):
        return EraseResult(True, "Đã gửi lệnh xóa. iPhone sẽ khởi động lại và về màn hình Hello.", output)

    try:
        if udid not in list_udids():
            return EraseResult(True, "iPhone đã ngắt kết nối sau khi nhận lệnh xóa.", output)
    except RuntimeError:
        pass

    return EraseResult(False, f"Không thể gửi lệnh xóa, mã lỗi {result.returncode}.", output)
