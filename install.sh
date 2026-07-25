#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip python3-tk \
  build-essential pkg-config git autoconf automake libtool-bin \
  libplist-dev libimobiledevice-dev libxml2-dev libcurl4-openssl-dev \
  usbmuxd libimobiledevice-utils

if ! command -v ideviceactivation >/dev/null 2>&1; then
  echo "[INFO] Đang build libideviceactivation..."
  workdir="$(mktemp -d)"
  git clone https://github.com/libimobiledevice/libideviceactivation.git "$workdir/libideviceactivation"
  cd "$workdir/libideviceactivation"
  ./autogen.sh
  make -j"$(nproc)"
  sudo make install
  sudo ldconfig
fi

cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
chmod +x run.sh

echo
echo "Cài đặt hoàn tất. Chạy tool bằng: ./run.sh"
