from __future__ import annotations

import json
from dataclasses import dataclass

from .command import run_command


MODEL_MAPPING = {
    # iPhone X
    "iPhone10,3": "iPhone X",
    "iPhone10,6": "iPhone X",
    # iPhone XS / XS Max / XR
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max",
    "iPhone11,8": "iPhone XR",
    # iPhone 11 / 11 Pro / 11 Pro Max
    "iPhone12,1": "iPhone 11",
    "iPhone12,3": "iPhone 11 Pro",
    "iPhone12,5": "iPhone 11 Pro Max",
    # iPhone SE 2nd Gen
    "iPhone12,8": "iPhone SE (2nd Gen)",
    # iPhone 12 / 12 mini / 12 Pro / 12 Pro Max
    "iPhone13,1": "iPhone 12 mini",
    "iPhone13,2": "iPhone 12",
    "iPhone13,3": "iPhone 12 Pro",
    "iPhone13,4": "iPhone 12 Pro Max",
    # iPhone 13 / 13 mini / 13 Pro / 13 Pro Max
    "iPhone14,4": "iPhone 13 mini",
    "iPhone14,5": "iPhone 13",
    "iPhone14,2": "iPhone 13 Pro",
    "iPhone14,3": "iPhone 13 Pro Max",
    # iPhone SE 3rd Gen
    "iPhone14,6": "iPhone SE (3rd Gen)",
    # iPhone 14 / 14 Plus / 14 Pro / 14 Pro Max
    "iPhone14,7": "iPhone 14",
    "iPhone14,8": "iPhone 14 Plus",
    "iPhone15,2": "iPhone 14 Pro",
    "iPhone15,3": "iPhone 14 Pro Max",
    # iPhone 15 / 15 Plus / 15 Pro / 15 Pro Max
    "iPhone15,4": "iPhone 15",
    "iPhone15,5": "iPhone 15 Plus",
    "iPhone16,1": "iPhone 15 Pro",
    "iPhone16,2": "iPhone 15 Pro Max",
    # iPhone 16 / 16 Plus / 16 Pro / 16 Pro Max
    "iPhone17,3": "iPhone 16",
    "iPhone17,4": "iPhone 16 Plus",
    "iPhone17,1": "iPhone 16 Pro",
    "iPhone17,2": "iPhone 16 Pro Max",
}


@dataclass
class DeviceInfo:
    udid: str
    name: str = "iPhone"
    product_type: str = "Không rõ"
    ios_version: str = "Không rõ"
    connection_type: str = "USB"
    imei: str = "Không rõ"
    serial: str = "Không rõ"


def _extract_json(text: str):
    import re
    for match in re.finditer(r'\[', text):
        start = match.start()
        end = text.rfind(']')
        while end > start:
            try:
                candidate = text[start:end + 1]
                parsed = json.loads(candidate)
                if isinstance(parsed, (list, dict)):
                    return parsed
            except json.JSONDecodeError:
                pass
            end = text.rfind(']', 0, end)
    return None


def discover_devices() -> list[DeviceInfo]:
    devices: list[DeviceInfo] = []

    try:
        result = run_command(["pymobiledevice3", "usbmux", "list"], timeout=15)
        payload = _extract_json(result.combined)
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                product_type = str(item.get("ProductType", ""))
                device_class = str(item.get("DeviceClass", ""))
                if device_class and device_class.lower() != "iphone" and not product_type.startswith("iPhone"):
                    continue
                udid = str(
                    item.get("UniqueDeviceID")
                    or item.get("Identifier")
                    or item.get("SerialNumber")
                    or ""
                ).strip()
                if not udid:
                    continue
                devices.append(DeviceInfo(
                    udid=udid,
                    name=str(item.get("DeviceName") or "iPhone"),
                    product_type=product_type or "Không rõ",
                    ios_version=str(item.get("ProductVersion") or "Không rõ"),
                    connection_type=str(item.get("ConnectionType") or "USB"),
                ))
    except RuntimeError:
        pass

    if not devices:
        result = run_command(["idevice_id", "-l"], timeout=15, check=False)
        for line in result.stdout.splitlines():
            udid = line.strip()
            if udid:
                devices.append(DeviceInfo(udid=udid))

    # Bổ sung thông tin chi tiết qua lệnh ideviceinfo
    for d in devices:
        raw_product = d.product_type
        if raw_product in MODEL_MAPPING:
            d.product_type = f"{MODEL_MAPPING[raw_product]} ({raw_product})"

        try:
            info_res = run_command(["ideviceinfo", "-u", d.udid], timeout=5, check=False)
            if info_res.returncode == 0:
                info = {}
                for line in info_res.stdout.splitlines():
                    if ":" in line:
                        parts = line.split(":", 1)
                        info[parts[0].strip()] = parts[1].strip()

                if "DeviceName" in info:
                    d.name = info["DeviceName"]
                if "ProductType" in info:
                    prod = info["ProductType"]
                    d.product_type = f"{MODEL_MAPPING.get(prod, prod)} ({prod})" if prod in MODEL_MAPPING else prod
                if "ProductVersion" in info:
                    d.ios_version = info["ProductVersion"]

                d.imei = info.get("InternationalMobileEquipmentIdentity") or info.get("IMEI") or "Không rõ"
                d.serial = info.get("SerialNumber") or "Không rõ"
        except Exception:
            pass

    return devices
