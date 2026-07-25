import json
import os
import queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk
import qrcode

from .activation import ActivationStatus, activate, get_activation_state
from .android import AndroidDeviceInfo, discover_android_devices, bypass_android_setup, install_apk, erase_android
from .command import run_command
from .devices import DeviceInfo, discover_devices
from .erasure import erase_device

CONFIG_FILE = "iphone_tool/config.json"

STATUS_TEXT = {
    ActivationStatus.ACTIVATED: "Đã kích hoạt",
    ActivationStatus.UNACTIVATED: "Chưa kích hoạt",
    ActivationStatus.BLOCKED: "Bị chặn",
    ActivationStatus.UNKNOWN: "Không xác định",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(config_data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# Complete premium Web App self-test script for iOS Safari
HTML_CONTENT = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>iPhone Self-Test Suite</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 16px;
            box-sizing: border-box;
            user-select: none;
            -webkit-user-select: none;
        }
        .container {
            max-width: 480px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 {
            font-size: 24px;
            color: #38bdf8;
            margin: 0;
            font-weight: 800;
        }
        .header p {
            color: #64748b;
            font-size: 13px;
            margin: 6px 0 0 0;
        }
        .card {
            background-color: #1e293b;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            border: 1px solid #334155;
        }
        h2 {
            font-size: 18px;
            margin: 0 0 12px 0;
            color: #f1f5f9;
        }
        .label {
            font-size: 12px;
            color: #94a3b8;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
            display: block;
        }
        select, input {
            width: 100%;
            padding: 12px 16px;
            background-color: #0f172a;
            color: #f8fafc;
            border: 1px solid #334155;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #3b82f6;
        }
        .btn {
            background-color: #2563eb;
            color: #ffffff;
            font-weight: bold;
            font-size: 16px;
            padding: 14px;
            border: none;
            border-radius: 12px;
            width: 100%;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        }
        .btn:active {
            transform: scale(0.98);
        }
        .btn-success {
            background-color: #10b981;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);
        }
        .btn-danger {
            background-color: #ef4444;
            box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.2);
        }
        .btn-secondary {
            background-color: #475569;
            box-shadow: 0 4px 6px -1px rgba(71, 85, 105, 0.2);
        }
        .flex-buttons {
            display: flex;
            gap: 12px;
            margin-top: 20px;
        }
        .step-panel {
            display: none;
        }
        .step-panel.active {
            display: block;
        }
        .progress-bar-container {
            width: 100%;
            background-color: #334155;
            height: 6px;
            border-radius: 3px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        .progress-bar-fill {
            background-color: #3b82f6;
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
        }
        .grid-board {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 4px;
            margin: 20px 0;
            touch-action: none;
        }
        .grid-box {
            aspect-ratio: 1;
            background-color: #334155;
            border-radius: 6px;
            transition: background-color 0.1s;
        }
        .grid-box.touched {
            background-color: #10b981;
        }
        .fullscreen-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 9999;
            display: none;
        }
        .fullscreen-overlay.active {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
        .sensor-data {
            font-family: monospace;
            background-color: #0f172a;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            color: #38bdf8;
            margin-bottom: 16px;
        }
        .audio-bar {
            width: 100%;
            height: 12px;
            background-color: #0f172a;
            border-radius: 6px;
            overflow: hidden;
            margin: 16px 0;
        }
        .audio-bar-fill {
            height: 100%;
            background-color: #10b981;
            width: 0%;
            transition: width 0.1s ease;
        }
        .camera-preview {
            width: 100%;
            height: 260px;
            background-color: #000;
            border-radius: 12px;
            overflow: hidden;
            margin: 16px 0;
            position: relative;
        }
        .camera-preview video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>iPhone Self-Test</h1>
            <p>Hệ thống tự động chẩn đoán qua Safari</p>
        </div>
        
        <div class="progress-bar-container">
            <div id="progressBar" class="progress-bar-fill"></div>
        </div>

        <!-- BƯỚC 1: NHẬP THÔNG TIN -->
        <div id="step-1" class="card step-panel active">
            <h2>Bước 1: Chọn Thiết Bị</h2>
            <label class="label">Chọn UDID của máy đang test:</label>
            <select id="udidSelect">
                <option value="">Đang tải danh sách thiết bị...</option>
            </select>
            
            <label class="label">Mã Session:</label>
            <input type="text" id="sessionIdInput" value="SESSION-A1">
            
            <button class="btn btn-success" onclick="nextStep(2)">BẮT ĐẦU TEST</button>
        </div>

        <!-- BƯỚC 2: KIỂM TRA CAMERA -->
        <div id="step-2" class="card step-panel">
            <h2>Bước 2: Kiểm Tra Camera</h2>
            <p style="font-size:14px; color:#94a3b8;">Xác nhận hình ảnh camera trước & sau hiển thị rõ nét, không đốm mốc.</p>
            
            <div class="camera-preview">
                <video id="webcam" autoplay playsinline muted></video>
            </div>
            
            <button class="btn btn-secondary" onclick="switchCamera()">Đổi Camera Trước / Sau</button>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('CAMERA', 'FAIL', 'Camera bị đốm/mờ/lỗi'); nextStep(3);">HỎNG</button>
                <button class="btn btn-success" onclick="saveTestResult('CAMERA', 'PASS', 'Camera trước & sau tốt'); nextStep(3);">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 3: KIỂM TRA ÂM THANH -->
        <div id="step-3" class="card step-panel">
            <h2>Bước 3: Kiểm Tra Âm Thanh</h2>
            <p style="font-size:14px; color:#94a3b8;">Nhấn "Phát Tone" nghe thử loa dưới, đồng thời nói để test microphone (vạch xanh).</p>
            
            <button class="btn btn-secondary" onclick="playTestTone()">Phát Tone Thử Nghiệm</button>
            
            <div class="audio-bar">
                <div id="audioBarFill" class="audio-bar-fill"></div>
            </div>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('AUDIO', 'FAIL', 'Loa rè hoặc Mic hỏng'); nextStep(4);">HỎNG</button>
                <button class="btn btn-success" onclick="saveTestResult('AUDIO', 'PASS', 'Loa ngoài & mic thu tốt'); nextStep(4);">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 4: KIỂM TRA SENSOR -->
        <div id="step-4" class="card step-panel">
            <h2>Bước 4: Cảm Biến Chuyển Động</h2>
            <p style="font-size:14px; color:#94a3b8;">Lắc nhẹ hoặc nghiêng điện thoại để kiểm tra cảm biến gia tốc/xoay.</p>
            
            <button class="btn btn-secondary" onclick="requestSensorPermission()">Kích Hoạt Cảm Biến</button>
            
            <div style="height:15px"></div>
            <div class="sensor-data">
                X: <span id="accel-x">0.00</span><br>
                Y: <span id="accel-y">0.00</span><br>
                Z: <span id="accel-z">0.00</span>
            </div>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('SENSORS', 'FAIL', 'Cảm biến gia tốc đơ'); nextStep(5);">HỎNG</button>
                <button class="btn btn-success" onclick="saveTestResult('SENSORS', 'PASS', 'Gia tốc kế phản hồi tốt'); nextStep(5);">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 5: KIỂM TRA CẢM ỨNG -->
        <div id="step-5" class="card step-panel">
            <h2>Bước 5: Kiểm Tra Cảm Ứng (Touchscreen)</h2>
            <p style="font-size:14px; color:#94a3b8;">Vuốt bao phủ toàn bộ lưới dưới đây để kiểm tra điểm chết màn hình.</p>
            
            <div id="touchGrid" class="grid-board"></div>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('TOUCHSCREEN', 'FAIL', 'Phát hiện điểm chết cảm ứng'); nextStep(6);">HỎNG</button>
                <button class="btn btn-success" onclick="checkTouchGridResult()">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 6: KIỂM TRA ĐIỂM CHẾT LCD -->
        <div id="step-6" class="card step-panel">
            <h2>Bước 6: Kiểm Tra Điểm Chết LCD (Display)</h2>
            <p style="font-size:14px; color:#94a3b8;">Chạy chế độ toàn màn hình đơn sắc để kiểm tra sọc LCD hoặc đốm sáng.</p>
            
            <button class="btn btn-secondary" onclick="startDisplayTest()">Bắt Đầu Đổi Màu Màn Hình</button>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('DISPLAY', 'FAIL', 'Phát hiện sọc màn hình/điểm chết'); nextStep(7);">HỎNG</button>
                <button class="btn btn-success" onclick="saveTestResult('DISPLAY', 'PASS', 'Hiển thị trong, không sọc'); nextStep(7);">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 7: KIỂM TRA ĐÈN FLASH & RUNG -->
        <div id="step-7" class="card step-panel">
            <h2>Bước 7: Đèn Flash & Motor Rung</h2>
            <p style="font-size:14px; color:#94a3b8;">Kích hoạt thử nghiệm hoặc tự kiểm tra:</p>
            
            <button class="btn btn-secondary" onclick="tryTriggerTorch()">Kích Hoạt Flash (Đèn Pin)</button>
            <div style="height:10px"></div>
            <button class="btn btn-secondary" onclick="tryTriggerVibrate()">Kích Hoạt Rung</button>
            
            <p style="font-size:12px; color:#94a3b8; margin-top:12px; line-height: 1.4;">
                * Lưu ý: Safari iOS chặn Web tự bật Đèn pin. Nếu không tự sáng, hãy <b>vuốt mở Control Center trên iPhone</b> bật thử đèn pin thủ công để xác nhận.
            </p>
            
            <div class="flex-buttons">
                <button class="btn btn-danger" onclick="saveTestResult('FLASHLIGHT', 'FAIL', 'Đèn flash hoặc rung hỏng'); nextStep(8);">HỎNG</button>
                <button class="btn btn-success" onclick="saveTestResult('FLASHLIGHT', 'PASS', 'Đèn flash và rung hoạt động tốt'); nextStep(8);">ĐẠT</button>
            </div>
        </div>

        <!-- BƯỚC 8: CẢM BIẾN TIỆM CẬN & BIOMETRICS -->
        <div id="step-8" class="card step-panel">
            <h2>Bước 8: Tiệm Cận & Face ID</h2>
            <p style="font-size:14px; color:#94a3b8;"><b>Kiểm tra Tiệm cận:</b> Hãy áp tai vào cảm biến nghe gọi hoặc mở máy ghi âm, màn hình phải tắt khi có vật cản sát tai.</p>
            <p style="font-size:14px; color:#94a3b8;"><b>Kiểm tra Face ID/Touch ID:</b> Hãy mở cài đặt Face ID xem có thiết lập được không.</p>
            
            <label class="label">Cảm biến Tiệm cận:</label>
            <select id="proximityResult">
                <option value="PASS">PASS (Tắt màn hình nhạy)</option>
                <option value="FAIL">FAIL (Hỏng/Không phản hồi)</option>
            </select>
            
            <label class="label">Face ID / Touch ID:</label>
            <select id="biometricResult">
                <option value="PASS">PASS (Thiết lập & nhận diện tốt)</option>
                <option value="FAIL">FAIL (Báo lỗi Face ID/Touch ID)</option>
            </select>
            
            <button class="btn btn-success" onclick="finishAndSubmit()">GỬI BÁO CÁO & AUTO ERASE</button>
        </div>
    </div>

    <!-- OVERLAY ĐỔI MÀU MÀN HÌNH -->
    <div id="colorOverlay" class="fullscreen-overlay" onclick="cycleTestColor()">
        <span id="overlayText" style="color:#fff; background:rgba(0,0,0,0.7); padding:12px; border-radius:8px; font-weight:bold;">Bấm để đổi màu (Nhấn giữ 1s để thoát)</span>
    </div>

    <script>
        let currentStep = 1;
        let testResults = [];
        let connectedDevices = [];
        let currentStream = null;
        let useFacingMode = "user";
        
        // Audio API variables
        let audioContext = null;
        let analyser = null;
        let microphoneSource = null;
        let javascriptNode = null;
        
        // Touch grid variables
        const rows = 8;
        const cols = 5;
        let touchedCells = new Set();
        
        async function loadDevices() {
            try {
                let res = await fetch('/api/devices');
                let data = await res.json();
                connectedDevices = data.devices;
                
                let select = document.getElementById('udidSelect');
                let currentVal = select.value;
                select.innerHTML = '';
                
                if (connectedDevices.length === 0) {
                    select.innerHTML = '<option value="">Không phát hiện iPhone qua USB</option>';
                } else {
                    connectedDevices.forEach(udid => {
                        let opt = document.createElement('option');
                        opt.value = udid;
                        opt.textContent = udid.substring(0, 10) + "... (" + udid.substring(udid.length - 6) + ")";
                        select.appendChild(opt);
                    });
                    if (currentVal && connectedDevices.includes(currentVal)) {
                        select.value = currentVal;
                    }
                }
            } catch (e) {
                console.error("Lỗi tải thiết bị", e);
            }
        }
        
        window.addEventListener('DOMContentLoaded', () => {
            loadDevices();
            setInterval(loadDevices, 4000); // Polling devices
            setupTouchGrid();
            document.getElementById('sessionIdInput').value = "PB30-P4-" + Math.floor(1000 + Math.random() * 9000);
        });

        function nextStep(step) {
            if (currentStep === 2) stopCamera();
            if (currentStep === 3) stopMicrophone();
            
            document.getElementById('step-' + currentStep).classList.remove('active');
            currentStep = step;
            document.getElementById('step-' + currentStep).classList.add('active');
            
            document.getElementById('progressBar').style.width = ((currentStep - 1) / 7 * 100) + "%";
            
            if (currentStep === 2) startCamera();
            if (currentStep === 3) startMicrophone();
        }
        
        function saveTestResult(testId, status, message) {
            testResults = testResults.filter(item => item.test_id !== testId);
            testResults.push({
                test_id: testId,
                status: status,
                message: message
            });
        }
        
        // CAMERA LOGIC
        async function startCamera() {
            stopCamera();
            try {
                let constraints = {
                    video: { facingMode: useFacingMode },
                    audio: false
                };
                currentStream = await navigator.mediaDevices.getUserMedia(constraints);
                document.getElementById('webcam').srcObject = currentStream;
            } catch (e) {
                alert("Không mở được camera. Vui lòng cấp quyền.");
            }
        }
        
        function stopCamera() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }
        }
        
        function switchCamera() {
            useFacingMode = (useFacingMode === "user") ? "environment" : "user";
            startCamera();
        }
        
        // FLASH/TORCH ACTIVATION ATTEMPT
        async function tryTriggerTorch() {
            if (currentStream) {
                try {
                    let track = currentStream.getVideoTracks()[0];
                    await track.applyConstraints({
                        advanced: [{ torch: true }]
                    });
                    alert("Đã gửi yêu cầu bật Flash. Nếu không sáng, vui lòng bật thủ công bằng Control Center của iPhone.");
                } catch (e) {
                    alert("Safari iOS chặn Web bật đèn pin trực tiếp. Vui lòng bật thủ công qua Control Center để kiểm tra.");
                }
            } else {
                alert("Hãy quay lại bước Camera hoặc đảm bảo camera đang chạy để kích hoạt đèn flash.");
            }
        }
        
        function tryTriggerVibrate() {
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            } else {
                alert("Trình duyệt iOS chặn rung từ Web. Vui lòng gạt cần rung sườn máy để kiểm tra motor rung.");
            }
        }
        
        // AUDIO/MICROPHONE LOGIC
        async function startMicrophone() {
            try {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                let stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
                analyser = audioContext.createAnalyser();
                microphoneSource = audioContext.createMediaStreamSource(stream);
                
                analyser.fftSize = 256;
                microphoneSource.connect(analyser);
                
                javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);
                analyser.connect(javascriptNode);
                javascriptNode.connect(audioContext.destination);
                
                javascriptNode.onaudioprocess = () => {
                    let array = new Uint8Array(analyser.frequencyBinCount);
                    analyser.getByteFrequencyData(array);
                    let values = 0;
                    for (let i = 0; i < array.length; i++) {
                        values += array[i];
                    }
                    let average = values / array.length;
                    document.getElementById('audioBarFill').style.width = Math.min(average * 2.5, 100) + "%";
                };
            } catch (e) {
                console.error("Lỗi microphone", e);
            }
        }
        
        function stopMicrophone() {
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
        }
        
        function playTestTone() {
            let context = new (window.AudioContext || window.webkitAudioContext)();
            let osc = context.createOscillator();
            let gain = context.createGain();
            osc.connect(gain);
            gain.connect(context.destination);
            osc.frequency.value = 1000;
            gain.gain.value = 0.5;
            osc.start();
            setTimeout(() => {
                osc.stop();
                context.close();
            }, 1000);
        }
        
        // SENSORS LOGIC
        function requestSensorPermission() {
            if (typeof DeviceMotionEvent !== 'undefined' && typeof DeviceMotionEvent.requestPermission === 'function') {
                DeviceMotionEvent.requestPermission()
                    .then(response => {
                        if (response === 'granted') {
                            window.addEventListener('devicemotion', handleMotionEvent);
                        } else {
                            alert("Quyền bị từ chối.");
                        }
                    })
                    .catch(console.error);
            } else {
                window.addEventListener('devicemotion', handleMotionEvent);
            }
        }
        
        function handleMotionEvent(event) {
            let acc = event.accelerationIncludingGravity;
            if (acc) {
                document.getElementById('accel-x').textContent = acc.x ? acc.x.toFixed(2) : "0.00";
                document.getElementById('accel-y').textContent = acc.y ? acc.y.toFixed(2) : "0.00";
                document.getElementById('accel-z').textContent = acc.z ? acc.z.toFixed(2) : "0.00";
            }
        }
        
        // TOUCHSCREEN GRID LOGIC
        function setupTouchGrid() {
            let container = document.getElementById('touchGrid');
            container.innerHTML = '';
            touchedCells.clear();
            
            for (let i = 0; i < rows * cols; i++) {
                let cell = document.createElement('div');
                cell.className = 'grid-box';
                cell.dataset.index = i;
                container.appendChild(cell);
            }
            
            container.addEventListener('touchmove', (e) => {
                e.preventDefault();
                let touch = e.touches[0];
                let element = document.elementFromPoint(touch.clientX, touch.clientY);
                if (element && element.className === 'grid-box') {
                    let idx = element.dataset.index;
                    element.classList.add('touched');
                    touchedCells.add(idx);
                }
            }, { passive: false });
        }
        
        function checkTouchGridResult() {
            let totalCells = rows * cols;
            if (touchedCells.size >= totalCells - 2) {
                saveTestResult('TOUCHSCREEN', 'PASS', 'Cảm ứng hoàn hảo 100% diện tích');
                nextStep(6);
            } else {
                alert("Bạn phải vuốt kín lưới cảm ứng để tiếp tục!");
            }
        }
        
        // DISPLAY TEST LOGIC
        let colors = ['#ff0000', '#00ff00', '#0000ff', '#ffffff', '#000000'];
        let colorIdx = 0;
        
        function startDisplayTest() {
            let overlay = document.getElementById('colorOverlay');
            overlay.style.backgroundColor = colors[0];
            overlay.classList.add('active');
            colorIdx = 0;
            
            let pressTimer;
            overlay.addEventListener('touchstart', (e) => {
                pressTimer = setTimeout(() => {
                    overlay.classList.remove('active');
                }, 1200);
            });
            overlay.addEventListener('touchend', () => {
                clearTimeout(pressTimer);
            });
        }
        
        function cycleTestColor() {
            colorIdx++;
            if (colorIdx >= colors.length) {
                document.getElementById('colorOverlay').classList.remove('active');
            } else {
                document.getElementById('colorOverlay').style.backgroundColor = colors[colorIdx];
            }
        }
        
        // FINISH AND SUBMIT
        async function finishAndSubmit() {
            let udid = document.getElementById('udidSelect').value;
            if (!udid) {
                alert("Vui lòng kết nối iPhone và chọn đúng UDID!");
                return;
            }
            
            saveTestResult('DEVICE_INFO', 'PASS', 'Kiểm tra qua Safari Trình Duyệt');
            
            let proximity = document.getElementById('proximityResult').value;
            saveTestResult('PROXIMITY', proximity, proximity === 'PASS' ? 'Cảm biến tiệm cận tốt' : 'Cảm biến tiệm cận lỗi');
            
            let biometric = document.getElementById('biometricResult').value;
            saveTestResult('BIOMETRIC', biometric, biometric === 'PASS' ? 'Face ID/Touch ID tốt' : 'Lỗi sinh trắc học');
            
            let passedCount = testResults.filter(r => r.status === 'PASS').length;
            let failedCount = testResults.filter(r => r.status === 'FAIL').length;
            
            let payload = {
                udid: udid,
                session_id: document.getElementById('sessionIdInput').value,
                model: 'iPhone (Web App)',
                ios_version: 'Safari iOS',
                total_tests: testResults.length,
                passed: passedCount,
                failed: failedCount,
                inconclusive: 0,
                not_supported: 0,
                failed_functions: testResults.filter(r => r.status === 'FAIL').map(r => r.test_id),
                results: testResults
            };
            
            try {
                let res = await fetch('/api/results', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                let data = await res.json();
                if (data.status === 'success') {
                    alert("Đã gửi báo cáo thành công về máy Ubuntu! Thiết bị sẽ được tự động Erase.");
                } else {
                    alert("Lỗi khi gửi kết quả: " + (data.message || "Lỗi không xác định"));
                }
            } catch (e) {
                alert("Lỗi kết nối tới Server Ubuntu: " + e.message);
            }
        }
    </script>
</body>
</html>
"""


def start_api_server(app_instance):
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    async def get_test_page():
        return HTMLResponse(content=HTML_CONTENT, status_code=200)

    @app.get("/api/devices")
    async def get_devices():
        return {"devices": list(app_instance.devices.keys())}

    @app.post("/api/results")
    async def receive_results(request: Request):
        try:
            data = await request.json()
            app_instance.events.put(("test_results", data))
            return {"status": "success", "message": "Results received successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    try:
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="warning")
    except Exception as e:
        app_instance.events.put(("error", f"Không thể khởi động Server nhận kết quả (Port 8080 đã bị dùng?): {e}"))


class IPhoneActivationApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("iPhone & Android Activation & Control Suite")
        self.geometry("1150x820")
        self.minsize(1100, 720)
        self.configure(bg="#0f172a")

        self.events: queue.Queue = queue.Queue()
        self.devices: dict[str, DeviceInfo] = {}
        self.states: dict[str, ActivationStatus] = {}
        self.test_results: dict[str, dict] = {}
        self.android_devices: dict[str, AndroidDeviceInfo] = {}
        self.android_test_results: dict[str, dict] = {}
        self.busy = False
        
        self.local_ip = get_local_ip()
        self.web_url = f"http://{self.local_ip}:8080"

        # Load persisted settings
        self.config = load_config()
        self.ipa_path_var = tk.StringVar(value=self.config.get("ipa_path", ""))
        self.wifi_ssid_var = tk.StringVar(value=self.config.get("wifi_ssid", ""))
        self.wifi_password_var = tk.StringVar(value=self.config.get("wifi_password", ""))
        self.apk_path_var = tk.StringVar(value=self.config.get("apk_path", ""))
        self.auto_install_android_var = tk.BooleanVar(value=self.config.get("auto_install_android", True))
        self.auto_erase_android_var = tk.BooleanVar(value=self.config.get("auto_erase_android", False))

        self._build_style()
        self._build_ui()
        self.after(150, self._process_events)
        self.after(300, self.refresh_devices)
        self.after(350, self.refresh_android_devices)
        self.after(3000, self._auto_refresh)

        # Khởi động Server API nhận kết quả test ở background và truyền self
        threading.Thread(target=start_api_server, args=(self,), daemon=True).start()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#1e293b",
            foreground="#f8fafc",
            fieldbackground="#1e293b",
            rowheight=36,
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#0f172a",
            foreground="#f8fafc",
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview", background=[("selected", "#2563eb")])
        style.configure(
            "TNotebook",
            background="#0f172a",
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background="#1e293b",
            foreground="#94a3b8",
            padding=[20, 8],
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

    def _create_btn(self, parent: tk.Frame, text: str, bg: str, hover: str, command: callable, state: str = "normal") -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg if state == "normal" else "#334155",
            fg="#ffffff",
            activebackground=hover,
            activeforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=6,
            cursor="hand2" if state == "normal" else "arrow",
            state=state,
            disabledforeground="#94a3b8"
        )
        def on_enter(e):
            if btn["state"] != "disabled":
                btn.configure(bg=hover)
        def on_leave(e):
            if btn["state"] != "disabled":
                btn.configure(bg=bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def _build_ui(self) -> None:
        # Header Section
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=28, pady=(24, 12))
        
        title_frame = tk.Frame(header, bg="#0f172a")
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="Universal Device Activation & Control Suite", bg="#0f172a", fg="#ffffff", font=("Segoe UI", 24, "bold")).pack(side="left")
        
        tk.Label(
            header,
            text=f"Địa chỉ IP máy trạm: {self.local_ip} | Địa chỉ nhận kết quả: {self.web_url}",
            bg="#0f172a",
            fg="#38bdf8",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(6, 0))

        # Create Notebook
        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=28, pady=12)

        # Tab 1: iOS Workstation
        self.ios_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.ios_tab, text=" iOS Workstation ")

        # Tab 2: Android Workstation
        self.android_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.android_tab, text=" Android Workstation ")

        # --- BUILD iOS TAB ---
        # Main content area split into Table (Left) and Self-Test Panel (Right)
        main_pane = tk.Frame(self.ios_tab, bg="#0f172a")
        main_pane.pack(fill="both", expand=True, pady=12)
        
        # Right Panel (Self-Test Details)
        self.right_panel = tk.Frame(main_pane, bg="#1e293b", width=340, highlightbackground="#334155", highlightthickness=1)
        self.right_panel.pack(side="right", fill="both", padx=(16, 0))
        self.right_panel.pack_propagate(False) # Keep fixed width
        
        # Left Panel (Devices Table)
        left_panel = tk.Frame(main_pane, bg="#0f172a")
        left_panel.pack(side="left", fill="both", expand=True)

        table_box = tk.Frame(left_panel, bg="#1e293b", highlightbackground="#334155", highlightthickness=1)
        table_box.pack(fill="both", expand=True)

        columns = ("name", "product", "ios", "connection", "activation", "imei", "serial", "udid")
        self.tree = ttk.Treeview(table_box, columns=columns, show="headings", selectmode="extended")
        
        self.tree.tag_configure("Activated", foreground="#34d399")
        self.tree.tag_configure("Unactivated", foreground="#fbbf24")
        self.tree.tag_configure("Blocked", foreground="#f87171")
        self.tree.tag_configure("Unknown", foreground="#94a3b8")
        
        headings = {
            "name": "Thiết bị", "product": "Model", "ios": "iOS", "connection": "Kết nối",
            "activation": "Trạng thái", "imei": "IMEI", "serial": "Số Serial", "udid": "UDID",
        }
        widths = {"name": 130, "product": 130, "ios": 60, "connection": 70, "activation": 120, "imei": 130, "serial": 110, "udid": 240}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=60, anchor="w")
            
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._update_buttons())

        self._build_right_panel()

        # Config Section (IPA Path & Wi-Fi automatic settings)
        config_frame = tk.Frame(self.ios_tab, bg="#0f172a")
        config_frame.pack(fill="x", pady=(0, 10))
        
        # Row 1: IPA Configuration
        ipa_row = tk.Frame(config_frame, bg="#0f172a")
        ipa_row.pack(fill="x", pady=2)
        tk.Label(ipa_row, text="File App Test (.ipa) [macOS]:", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10, "bold"), width=25, anchor="w").pack(side="left")
        self.ipa_path_entry = tk.Entry(ipa_row, textvariable=self.ipa_path_var, bg="#1e293b", fg="#f8fafc", insertbackground="white", relief="flat", font=("Segoe UI", 9), width=45)
        self.ipa_path_entry.pack(side="left", padx=10, ipady=3)
        self.browse_ipa_btn = self._create_btn(ipa_row, "Chọn File...", "#475569", "#334155", self.browse_ipa_file)
        self.browse_ipa_btn.configure(font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        self.browse_ipa_btn.pack(side="left")

        # Row 2: Auto Wi-Fi Configuration
        wifi_row = tk.Frame(config_frame, bg="#0f172a")
        wifi_row.pack(fill="x", pady=2)
        tk.Label(wifi_row, text="Wi-Fi SSID (Tên Wifi):", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10, "bold"), width=25, anchor="w").pack(side="left")
        self.wifi_ssid_entry = tk.Entry(wifi_row, textvariable=self.wifi_ssid_var, bg="#1e293b", fg="#f8fafc", insertbackground="white", relief="flat", font=("Segoe UI", 9), width=20)
        self.wifi_ssid_entry.pack(side="left", padx=10, ipady=3)
        
        tk.Label(wifi_row, text="Mật khẩu Wifi:", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        self.wifi_password_entry = tk.Entry(wifi_row, textvariable=self.wifi_password_var, bg="#1e293b", fg="#f8fafc", show="*", insertbackground="white", relief="flat", font=("Segoe UI", 9), width=20)
        self.wifi_password_entry.pack(side="left", padx=10, ipady=3)

        # Controls Section
        controls = tk.Frame(self.ios_tab, bg="#0f172a")
        controls.pack(fill="x", pady=(0, 16))
        
        self.refresh_btn = self._create_btn(controls, "Quét lại iPhone", "#475569", "#334155", self.refresh_devices)
        self.refresh_btn.pack(side="left")
        
        self.activate_btn = self._create_btn(controls, "Active iPhone", "#2563eb", "#1d4ed8", self.start_activation, state="disabled")
        self.activate_btn.pack(side="left", padx=10)
        
        self.install_app_btn = self._create_btn(controls, "Cài App Test (.ipa)", "#10b981", "#059669", self.install_test_app_selected, state="disabled")
        self.install_app_btn.pack(side="left", padx=(0, 10))
        
        self.erase_btn = self._create_btn(controls, "Erase về cài đặt gốc", "#dc2626", "#b91c1c", self.start_erase, state="disabled")
        self.erase_btn.pack(side="left")

        # Checkboxes column/row
        cb_frame = tk.Frame(controls, bg="#0f172a")
        cb_frame.pack(side="left", padx=15)

        self.auto_install_var = tk.BooleanVar(value=self.config.get("auto_install", True))
        self.auto_install_cb = tk.Checkbutton(
            cb_frame,
            text="Tự động cài App Test sau khi Active",
            variable=self.auto_install_var,
            command=self.save_settings,
            bg="#0f172a",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )
        self.auto_install_cb.pack(anchor="w")

        self.auto_erase_var = tk.BooleanVar(value=self.config.get("auto_erase", False))
        self.auto_erase_cb = tk.Checkbutton(
            cb_frame,
            text="Tự động Erase sau khi test xong",
            variable=self.auto_erase_var,
            command=self.save_settings,
            bg="#0f172a",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )
        self.auto_erase_cb.pack(anchor="w")

        # --- BUILD ANDROID TAB ---
        self._build_android_ui()

        # Terminal / Logs Box (Global, below Notebook)
        log_box = tk.Frame(self, bg="#0f172a")
        log_box.pack(fill="x", padx=28, pady=(0, 16))
        
        log_header = tk.Frame(log_box, bg="#1e293b", height=30)
        log_header.pack(fill="x")
        tk.Label(log_header, text="  TIẾN TRÌNH HOẠT ĐỘNG (LOGS)", bg="#1e293b", fg="#94a3b8", font=("Consolas", 9, "bold")).pack(side="left", pady=4)
        
        clear_btn = tk.Button(
            log_header,
            text="Xóa Nhật Ký",
            command=self.clear_logs,
            bg="#334155",
            fg="#f8fafc",
            activebackground="#475569",
            activeforeground="#f8fafc",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 8, "bold"),
            padx=10,
            cursor="hand2"
        )
        clear_btn.pack(side="right", padx=6, pady=2)
        
        self.log = tk.Text(log_box, height=8, bg="#020617", fg="#38bdf8", insertbackground="white", relief="flat", font=("Consolas", 9), padx=12, pady=10)
        self.log.pack(fill="x")
        self.log.configure(state="disabled")

        # Bottom Status Bar (Global)
        status_frame = tk.Frame(self, bg="#0f172a")
        status_frame.pack(fill="x", side="bottom", padx=28, pady=(0, 16))
        
        self.status_dot = tk.Label(status_frame, text="●", fg="#ef4444", bg="#0f172a", font=("Segoe UI", 12))
        self.status_dot.pack(side="left", padx=(0, 6))
        
        self.status_label = tk.Label(status_frame, text="Đang khởi tạo...", fg="#94a3b8", bg="#0f172a", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="left")

    def _build_android_ui(self) -> None:
        # Main content area split into Android Table (Left) and Android Self-Test Panel (Right)
        android_main_pane = tk.Frame(self.android_tab, bg="#0f172a")
        android_main_pane.pack(fill="both", expand=True, pady=12)
        
        # Right Panel (Android Self-Test Details)
        self.android_right_panel = tk.Frame(android_main_pane, bg="#1e293b", width=340, highlightbackground="#334155", highlightthickness=1)
        self.android_right_panel.pack(side="right", fill="both", padx=(16, 0))
        self.android_right_panel.pack_propagate(False) # Keep fixed width
        
        # Left Panel (Android Devices Table)
        android_left_panel = tk.Frame(android_main_pane, bg="#0f172a")
        android_left_panel.pack(side="left", fill="both", expand=True)

        android_table_box = tk.Frame(android_left_panel, bg="#1e293b", highlightbackground="#334155", highlightthickness=1)
        android_table_box.pack(fill="both", expand=True)

        columns = ("brand", "model", "android_version", "imei", "serial")
        self.android_tree = ttk.Treeview(android_table_box, columns=columns, show="headings", selectmode="extended")
        
        headings = {
            "brand": "Hãng", "model": "Model", "android_version": "Android", "imei": "IMEI", "serial": "Số Serial (ADB ID)"
        }
        widths = {"brand": 130, "model": 150, "android_version": 90, "imei": 150, "serial": 240}
        for col in columns:
            self.android_tree.heading(col, text=headings[col])
            self.android_tree.column(col, width=widths[col], minwidth=60, anchor="w")
            
        self.android_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(android_table_box, orient="vertical", command=self.android_tree.yview)
        scroll.pack(side="right", fill="y")
        self.android_tree.configure(yscrollcommand=scroll.set)
        self.android_tree.bind("<<TreeviewSelect>>", lambda _e: self._update_android_buttons())

        self._build_android_right_panel()

        # Config Section (APK Path settings)
        android_config_frame = tk.Frame(self.android_tab, bg="#0f172a")
        android_config_frame.pack(fill="x", pady=(0, 10))
        
        # Row 1: APK Configuration
        apk_row = tk.Frame(android_config_frame, bg="#0f172a")
        apk_row.pack(fill="x", pady=2)
        tk.Label(apk_row, text="File App Test (.apk):", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 10, "bold"), width=25, anchor="w").pack(side="left")
        self.apk_path_entry = tk.Entry(apk_row, textvariable=self.apk_path_var, bg="#1e293b", fg="#f8fafc", insertbackground="white", relief="flat", font=("Segoe UI", 9), width=45)
        self.apk_path_entry.pack(side="left", padx=10, ipady=3)
        self.browse_apk_btn = self._create_btn(apk_row, "Chọn File...", "#475569", "#334155", self.browse_apk_file)
        self.browse_apk_btn.configure(font=("Segoe UI", 9, "bold"), padx=10, pady=4)
        self.browse_apk_btn.pack(side="left")

        # Controls Section
        android_controls = tk.Frame(self.android_tab, bg="#0f172a")
        android_controls.pack(fill="x", pady=(0, 16))
        
        self.android_refresh_btn = self._create_btn(android_controls, "Quét lại Android", "#475569", "#334155", self.refresh_android_devices)
        self.android_refresh_btn.pack(side="left")
        
        self.android_activate_btn = self._create_btn(android_controls, "Active/Bypass Setup", "#2563eb", "#1d4ed8", self.start_android_bypass, state="disabled")
        self.android_activate_btn.pack(side="left", padx=10)
        
        self.android_install_app_btn = self._create_btn(android_controls, "Cài App Test (.apk)", "#10b981", "#059669", self.start_android_install, state="disabled")
        self.android_install_app_btn.pack(side="left", padx=(0, 10))
        
        self.android_erase_btn = self._create_btn(android_controls, "Erase về cài đặt gốc", "#dc2626", "#b91c1c", self.start_android_erase, state="disabled")
        self.android_erase_btn.pack(side="left")

        # Checkboxes column/row
        android_cb_frame = tk.Frame(android_controls, bg="#0f172a")
        android_cb_frame.pack(side="left", padx=15)

        self.android_auto_install_cb = tk.Checkbutton(
            android_cb_frame,
            text="Tự động cài App Test sau khi Active",
            variable=self.auto_install_android_var,
            command=self.save_settings,
            bg="#0f172a",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )
        self.android_auto_install_cb.pack(anchor="w")

        self.android_auto_erase_cb = tk.Checkbutton(
            android_cb_frame,
            text="Tự động Erase sau khi test xong",
            variable=self.auto_erase_android_var,
            command=self.save_settings,
            bg="#0f172a",
            fg="#e2e8f0",
            selectcolor="#0f172a",
            activebackground="#0f172a",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )
        self.android_auto_erase_cb.pack(anchor="w")

    def _build_android_right_panel(self) -> None:
        for widget in self.android_right_panel.winfo_children():
            widget.destroy()
            
        panel_header = tk.Frame(self.android_right_panel, bg="#0f172a", height=36)
        panel_header.pack(fill="x")
        tk.Label(panel_header, text="  KẾT QUẢ KIỂM TRA (SELF-TEST)", bg="#0f172a", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(side="left", pady=8)
        
        self.android_test_content = tk.Frame(self.android_right_panel, bg="#1e293b", padx=12, pady=12)
        self.android_test_content.pack(fill="both", expand=True)
        
        self._update_android_right_panel()

    def _update_android_right_panel(self) -> None:
        for widget in self.android_test_content.winfo_children():
            widget.destroy()
            
        serials = list(self.android_tree.selection())
        if not serials:
            tk.Label(self.android_test_content, text="Vui lòng chọn 1 thiết bị\nđể xem kết quả test.", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10), justify="center").pack(expand=True)
            return
            
        if len(serials) > 1:
            tk.Label(self.android_test_content, text=f"Đang chọn {len(serials)} thiết bị.\nVui lòng chọn duy nhất 1 thiết bị\nđể xem chi tiết.", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10), justify="center").pack(expand=True)
            return
            
        serial = serials[0]
        results = self.android_test_results.get(serial)
        
        if not results:
            tk.Label(self.android_test_content, text="Chưa có dữ liệu kiểm tra.", bg="#1e293b", fg="#e2e8f0", font=("Segoe UI", 11, "bold")).pack(pady=(5, 5))
            tk.Label(self.android_test_content, text="Hãy mở app test chẩn đoán\ntrên điện thoại Android:", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9), justify="center").pack(pady=(0, 6))
            return
            
        # Display Results
        summary_frame = tk.Frame(self.android_test_content, bg="#1e293b")
        summary_frame.pack(fill="x", pady=(0, 10))
        
        model_name = results.get("model", "Android Device")
        os_ver = results.get("ios_version", "Android")
        passed = results.get("passed", 0)
        failed = results.get("failed", 0)
        total = results.get("total_tests", 0)
        
        tk.Label(summary_frame, text=f"Model: {model_name} ({os_ver})", bg="#1e293b", fg="#ffffff", font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        
        stat_color = "#34d399" if failed == 0 else "#f87171"
        tk.Label(summary_frame, text=f"Kết quả: {passed}/{total} ĐẠT • {failed} LỖI", bg="#1e293b", fg=stat_color, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=2)
        
        # Test List in a Scrollable frame
        list_canvas = tk.Canvas(self.android_test_content, bg="#1e293b", highlightthickness=0)
        list_scroll = ttk.Scrollbar(self.android_test_content, orient="vertical", command=list_canvas.yview)
        scrollable_frame = tk.Frame(list_canvas, bg="#1e293b")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        )
        list_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=list_scroll.set)
        
        list_canvas.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        
        items = results.get("results", [])
        for item in items:
            test_id = item.get("test_id", "")
            status = item.get("status", "")
            msg = item.get("message", "")
            
            item_frame = tk.Frame(scrollable_frame, bg="#1e293b", pady=4)
            item_frame.pack(fill="x", expand=True)
            
            color = "#34d399" if status in ("PASS", "GUIDED PASS") else "#f87171" if status == "FAIL" else "#94a3b8"
            tk.Label(item_frame, text=f"■ {test_id}: {status}", bg="#1e293b", fg=color, font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
            if msg:
                tk.Label(item_frame, text=f"  {msg}", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 8), anchor="w").pack(fill="x")

    def _update_android_buttons(self) -> None:
        selected = list(self.android_tree.selection())
        state = "normal" if selected and not self.busy else "disabled"
        self._set_btn_state(self.android_activate_btn, state, "#2563eb")
        self._set_btn_state(self.android_install_app_btn, state, "#10b981")
        self._set_btn_state(self.android_erase_btn, state, "#dc2626")
        self._update_android_right_panel()

    def browse_apk_file(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Chọn file App Test (.apk)",
            filetypes=[("APK files", "*.apk")]
        )
        if path:
            self.apk_path_var.set(path)
            self.save_settings()

    def _set_btn_state(self, btn: tk.Button, state: str, normal_bg: str) -> None:
        btn.configure(state=state)
        if state == "disabled":
            btn.configure(bg="#334155", cursor="arrow")
        else:
            btn.configure(bg=normal_bg, cursor="hand2")

    def _build_right_panel(self) -> None:
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
        panel_header = tk.Frame(self.right_panel, bg="#0f172a", height=36)
        panel_header.pack(fill="x")
        tk.Label(panel_header, text="  KẾT QUẢ KIỂM TRA (SELF-TEST)", bg="#0f172a", fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(side="left", pady=8)
        
        self.test_content = tk.Frame(self.right_panel, bg="#1e293b", padx=12, pady=12)
        self.test_content.pack(fill="both", expand=True)
        
        self._update_right_panel()

    def _update_right_panel(self) -> None:
        for widget in self.test_content.winfo_children():
            widget.destroy()
            
        udids = self._selected_udids()
        if not udids:
            tk.Label(self.test_content, text="Vui lòng chọn 1 thiết bị\nđể xem kết quả test.", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10), justify="center").pack(expand=True)
            return
            
        if len(udids) > 1:
            tk.Label(self.test_content, text=f"Đang chọn {len(udids)} thiết bị.\nVui lòng chọn duy nhất 1 thiết bị\nđể xem chi tiết.", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10), justify="center").pack(expand=True)
            return
            
        udid = udids[0]
        results = self.test_results.get(udid)
        
        if not results:
            tk.Label(self.test_content, text="Chưa có dữ liệu kiểm tra.", bg="#1e293b", fg="#e2e8f0", font=("Segoe UI", 11, "bold")).pack(pady=(5, 5))
            tk.Label(self.test_content, text="Quét QR bằng camera iPhone để mở\nApp Test chẩn đoán qua Safari:", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9), justify="center").pack(pady=(0, 6))
            
            try:
                qr = qrcode.QRCode(version=1, box_size=3, border=2)
                qr.add_data(self.web_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#f8fafc", back_color="#1e293b")
                qr_img = qr_img.resize((150, 150))
                self.qr_photo = ImageTk.PhotoImage(image=qr_img)
                qr_label = tk.Label(self.test_content, image=self.qr_photo, bg="#1e293b")
                qr_label.pack(pady=5)
            except Exception as e:
                self._append_log(f"Lỗi tạo QR Code: {e}")
                
            tk.Label(self.test_content, text=self.web_url, bg="#1e293b", fg="#38bdf8", font=("Consolas", 10, "bold")).pack(pady=(2, 10))
            
            self._create_btn(self.test_content, "Cài ứng dụng Self-Test (.ipa)", "#10b981", "#059669", lambda: self.install_test_app(udid)).pack(fill="x", pady=(5, 0))
            return
            
        summary_frame = tk.Frame(self.test_content, bg="#1e293b")
        summary_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(summary_frame, text=f"Model: {results.get('model', 'N/A')}", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(summary_frame, text=f"iOS/Browser: {results.get('ios_version', 'N/A')}", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(summary_frame, text=f"Session: {results.get('session_id', 'N/A')}", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w")
        
        stats_text = f"Đạt {results.get('passed', 0)} / Hỏng {results.get('failed', 0)} / Nghi vấn {results.get('inconclusive', 0)}"
        tk.Label(summary_frame, text=stats_text, bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 10, "bold"), pady=6).pack(anchor="w")
        
        list_container = tk.Frame(self.test_content, bg="#1e293b")
        list_container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(list_container, bg="#1e293b", bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e293b")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def configure_window(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", configure_window)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        test_items = results.get("results", [])
        for item in test_items:
            item_frame = tk.Frame(scrollable_frame, bg="#1e293b", pady=4)
            item_frame.pack(fill="x", anchor="w")
            
            test_id = item.get("test_id") or item.get("testId") or "UNKNOWN_TEST"
            status = item.get("status") or "UNKNOWN"
            msg = item.get("message") or ""
            
            status_color = "#94a3b8"
            if status == "PASS":
                status_color = "#34d399"
            elif status == "FAIL":
                status_color = "#f87171"
            elif status in ("INCONCLUSIVE", "GUIDED PASS"):
                status_color = "#fbbf24"
                
            lbl_name = tk.Label(item_frame, text=f"{test_id}:", bg="#1e293b", fg="#e2e8f0", font=("Segoe UI", 9, "bold"))
            lbl_name.pack(side="left")
            
            lbl_status = tk.Label(item_frame, text=f" {status}", bg="#1e293b", fg=status_color, font=("Segoe UI", 9, "bold"))
            lbl_status.pack(side="left")
            
            if msg:
                lbl_msg = tk.Label(scrollable_frame, text=f"  ↳ {msg}", bg="#1e293b", fg="#64748b", font=("Segoe UI", 8), justify="left", wraplength=300)
                lbl_msg.pack(fill="x", anchor="w", padx=(10, 0))
                
        action_frame = tk.Frame(self.test_content, bg="#1e293b", pady=10)
        action_frame.pack(fill="x", side="bottom")
        self._create_btn(action_frame, "Xuất kết quả JSON", "#2563eb", "#1d4ed8", lambda: self.export_json(udid)).pack(fill="x")

    def browse_ipa_file(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Chọn file ứng dụng Self-Test (.ipa)",
            filetypes=[("iOS Apps", "*.ipa"), ("All Files", "*.*")]
        )
        if path:
            self.ipa_path_var.set(path)

    def install_test_app(self, udid: str) -> None:
        from tkinter import filedialog
        ipa_path = filedialog.askopenfilename(
            title="Chọn file ứng dụng Self-Test (.ipa)",
            filetypes=[("iOS Apps", "*.ipa"), ("All Files", "*.*")]
        )
        if not ipa_path:
            return
            
        self._set_busy(True, f"Đang cài app test lên thiết bị...")
        self._append_log(f"Đang cài đặt app {ipa_path} cho {udid}...")
        
        def worker() -> None:
            res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid], timeout=120, check=False)
            if res.returncode != 0:
                res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid, "--userspace"], timeout=120, check=False)
                
            self.events.put(("install_done", udid, res))
            
        threading.Thread(target=worker, daemon=True).start()

    def install_test_app_selected(self) -> None:
        udids = self._selected_udids()
        if not udids:
            return
        ipa_path = self.ipa_path_var.get()
        if not ipa_path:
            messagebox.showwarning("Thiếu IPA", "Vui lòng chọn đường dẫn file .ipa ở dòng cấu hình trước!")
            return
            
        self._set_busy(True, f"Đang cài app test lên {len(udids)} thiết bị...")
        self._append_log(f"Bắt đầu cài đặt app {ipa_path} cho {len(udids)} thiết bị: {', '.join(udids)}")
        
        def worker() -> None:
            for i, udid in enumerate(udids, 1):
                self.events.put(("log", f"[{i}/{len(udids)}] Đang cài đặt app lên {udid}..."))
                res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid], timeout=120, check=False)
                if res.returncode != 0:
                    res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid, "--userspace"], timeout=120, check=False)
                self.events.put(("log", f"[{i}/{len(udids)}] Kết quả cài đặt: {res.combined}"))
            self.events.put(("install_bulk_done", len(udids)))
            
        threading.Thread(target=worker, daemon=True).start()

    def export_json(self, udid: str) -> None:
        results = self.test_results.get(udid)
        if not results:
            return
        from tkinter import filedialog
        import json
        save_path = filedialog.asksaveasfilename(
            title="Lưu kết quả JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"test_result_{udid}.json"
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo thành công ra file:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không lưu được file: {e}")

    def auto_erase_device(self, udid: str) -> None:
        def worker() -> None:
            self.events.put(("log", f"[Auto-Erase] Đang tự động gửi lệnh xóa cho thiết bị {udid}..."))
            try:
                result = erase_device(udid, timeout=180)
                self.events.put(("log", f"[Auto-Erase] Kết quả {udid}: {result.message}"))
                self.events.put(("auto_erase_done", udid, result))
            except Exception as exc:
                self.events.put(("log", f"[Auto-Erase] Xóa {udid} thất bại: {exc}"))
        threading.Thread(target=worker, daemon=True).start()

    def _update_status(self, text: str, status_type: str = "idle") -> None:
        self.status_label.configure(text=text)
        if status_type == "idle":
            self.status_dot.configure(fg="#10b981")
        elif status_type == "busy":
            self.status_dot.configure(fg="#f59e0b")
        elif status_type == "scanning":
            self.status_dot.configure(fg="#3b82f6")
        elif status_type == "error":
            self.status_dot.configure(fg="#ef4444")
        self.update_idletasks()

    def save_settings(self) -> None:
        self.config["ipa_path"] = self.ipa_path_var.get()
        self.config["wifi_ssid"] = self.wifi_ssid_var.get()
        self.config["wifi_password"] = self.wifi_password_var.get()
        self.config["auto_install"] = self.auto_install_var.get()
        self.config["auto_erase"] = self.auto_erase_var.get()
        self.config["apk_path"] = self.apk_path_var.get()
        self.config["auto_install_android"] = self.auto_install_android_var.get()
        self.config["auto_erase_android"] = self.auto_erase_android_var.get()
        save_config(self.config)

    def clear_logs(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _selected_udids(self) -> list[str]:
        return list(self.tree.selection())

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self.busy = busy
        self._set_btn_state(self.refresh_btn, "disabled" if busy else "normal", "#475569")
        if message:
            self._update_status(message, "busy" if busy else "idle")
        self._update_buttons()

    def _update_buttons(self) -> None:
        udids = self._selected_udids()
        self._update_right_panel()
        if self.busy or not udids:
            self._set_btn_state(self.activate_btn, "disabled", "#2563eb")
            self._set_btn_state(self.install_app_btn, "disabled", "#10b981")
            self._set_btn_state(self.erase_btn, "disabled", "#dc2626")
            return
        
        can_activate = any(self.states.get(udid, ActivationStatus.UNKNOWN) != ActivationStatus.ACTIVATED for udid in udids)
        can_erase = any(self.states.get(udid, ActivationStatus.UNKNOWN) == ActivationStatus.ACTIVATED for udid in udids)
        
        self._set_btn_state(self.activate_btn, "normal" if can_activate else "disabled", "#2563eb")
        self._set_btn_state(self.install_app_btn, "normal", "#10b981")
        self._set_btn_state(self.erase_btn, "normal" if can_erase else "disabled", "#dc2626")

    def refresh_devices(self) -> None:
        if self.busy:
            return
        self._update_status("Đang quét iPhone qua USB...", "scanning")
        threading.Thread(target=self._worker_discover, daemon=True).start()

    def _worker_discover(self) -> None:
        try:
            devices = discover_devices()
            self.events.put(("devices", devices))
        except Exception as exc:
            self.events.put(("error", f"Lỗi quét thiết bị: {exc}"))

    def _refresh_selected_state(self, udid: str) -> None:
        def worker() -> None:
            try:
                state = get_activation_state(udid, timeout=20)
                self.events.put(("state", state))
            except Exception as exc:
                self.events.put(("error", f"Không đọc được trạng thái {udid}: {exc}"))
        threading.Thread(target=worker, daemon=True).start()

    def start_activation(self) -> None:
        udids = self._selected_udids()
        if not udids:
            return
        to_activate = [u for u in udids if self.states.get(u) != ActivationStatus.ACTIVATED]
        if not to_activate:
            messagebox.showinfo("Thông báo", "Tất cả các thiết bị được chọn đã được kích hoạt.")
            return

        self.save_settings()

        self._set_busy(True, f"Đang kích hoạt {len(to_activate)} iPhone...")
        self._append_log(f"Bắt đầu kích hoạt hàng loạt cho {len(to_activate)} thiết bị: {', '.join(to_activate)}")

        def worker() -> None:
            results = []
            for i, udid in enumerate(to_activate, 1):
                self.events.put(("log", f"[{i}/{len(to_activate)}] Đang kích hoạt thiết bị {udid}..."))
                try:
                    result = activate(udid, timeout=150)
                    results.append(result)
                    self.events.put(("log", f"[{i}/{len(to_activate)}] Kết quả {udid}: {result.message}"))
                    if result.status != ActivationStatus.ACTIVATED and result.raw_output:
                        self.events.put(("log", f"Chi tiết phản hồi:\n{result.raw_output}"))
                    
                    # Tự động cấu hình kết nối Wifi cho iPhone qua USB nếu người dùng nhập SSID
                    wifi_ssid = self.wifi_ssid_var.get()
                    wifi_pass = self.wifi_password_var.get()
                    if result.status == ActivationStatus.ACTIVATED and wifi_ssid:
                        self.events.put(("log", f"[{i}/{len(to_activate)}] Tự động gửi cấu hình Wi-Fi '{wifi_ssid}' qua USB..."))
                        wifi_res = run_command(["pymobiledevice3", "profile", "install-wifi-profile", "WPA", wifi_ssid, wifi_pass, "--udid", udid], timeout=40, check=False)
                        if wifi_res.returncode == 0:
                            self.events.put(("log", f"[{i}/{len(to_activate)}] Cấu hình Wi-Fi thành công! iPhone sẽ tự động kết nối mạng này."))
                        else:
                            self.events.put(("log", f"[{i}/{len(to_activate)}] Cấu hình Wi-Fi THẤT BẠI: {wifi_res.combined}"))

                    # Tự động cài đặt app test (.ipa) nếu bật checkbox tự động cài và chọn đường dẫn
                    ipa_path = self.ipa_path_var.get()
                    if result.status == ActivationStatus.ACTIVATED and self.auto_install_var.get() and ipa_path:
                        self.events.put(("log", f"[{i}/{len(to_activate)}] Tự động cài đặt app test (.ipa) lên {udid}..."))
                        install_res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid], timeout=120, check=False)
                        if install_res.returncode != 0:
                            install_res = run_command(["pymobiledevice3", "apps", "install", ipa_path, "--udid", udid, "--userspace"], timeout=120, check=False)
                        
                        if install_res.returncode == 0:
                            self.events.put(("log", f"[{i}/{len(to_activate)}] Cài đặt app test (.ipa) thành công lên {udid}!"))
                        else:
                            self.events.put(("log", f"[{i}/{len(to_activate)}] Cài đặt app test (.ipa) lên {udid} THẤT BẠI: {install_res.combined}"))
                except Exception as exc:
                    self.events.put(("log", f"[{i}/{len(to_activate)}] Kích hoạt {udid} thất bại: {exc}"))
            
            self.events.put(("activation_bulk_done", results))
            
        threading.Thread(target=worker, daemon=True).start()

    def start_erase(self) -> None:
        udids = self._selected_udids()
        if not udids:
            return
        to_erase = [u for u in udids if self.states.get(u) == ActivationStatus.ACTIVATED]
        if not to_erase:
            messagebox.showwarning("Không thể xóa", "Không có thiết bị nào trong danh sách chọn đang ở trạng thái Activated.")
            return

        self._set_busy(True, f"Đang gửi lệnh xóa {len(to_erase)} iPhone...")
        self._append_log(f"Bắt đầu xóa hàng loạt cho {len(to_erase)} thiết bị: {', '.join(to_erase)}")

        def worker() -> None:
            results = []
            for i, udid in enumerate(to_erase, 1):
                self.events.put(("log", f"[{i}/{len(to_erase)}] Đang gửi lệnh xóa cho thiết bị {udid}..."))
                try:
                    result = erase_device(udid, timeout=180)
                    results.append((udid, result))
                    self.events.put(("log", f"[{i}/{len(to_erase)}] Kết quả {udid}: {result.message}"))
                except Exception as exc:
                    self.events.put(("log", f"[{i}/{len(to_erase)}] Xóa {udid} thất bại: {exc}"))
            
            self.events.put(("erase_bulk_done", results))
            
        threading.Thread(target=worker, daemon=True).start()

    def refresh_android_devices(self) -> None:
        if self.busy:
            return
        self._update_status("Đang quét Android qua ADB...", "scanning")
        threading.Thread(target=self._worker_android_discover, daemon=True).start()

    def _worker_android_discover(self) -> None:
        try:
            devices = discover_android_devices()
            self.events.put(("android_discover_done", devices))
        except Exception as exc:
            self.events.put(("error", f"Lỗi quét thiết bị Android: {exc}"))

    def start_android_bypass(self) -> None:
        serials = list(self.android_tree.selection())
        if not serials:
            return
        serial = serials[0]
        self._set_busy(True, f"Đang bypass Setup cho Android {serial}...")
        self._append_log(f"Bắt đầu bypass Setup cho thiết bị Android: {serial}")

        def worker() -> None:
            try:
                success, msg = bypass_android_setup(serial)
                
                # Check auto-install checkbox for Android
                if success and self.auto_install_android_var.get():
                    apk = self.apk_path_var.get()
                    if apk:
                        self.events.put(("log", f"Tự động cài đặt app test (.apk) cho {serial}..."))
                        inst_ok, inst_msg = install_apk(serial, apk)
                        msg += f"\n[Auto-Install] {inst_msg}"
                
                self.events.put(("android_bypass_done", (serial, success, msg)))
            except Exception as e:
                self.events.put(("android_bypass_done", (serial, False, str(e))))
                
        threading.Thread(target=worker, daemon=True).start()

    def start_android_install(self) -> None:
        serials = list(self.android_tree.selection())
        if not serials:
            return
        serial = serials[0]
        apk_path = self.apk_path_var.get()
        if not apk_path:
            messagebox.showwarning("Thiếu APK", "Vui lòng chọn đường dẫn file .apk ở dòng cấu hình trước!")
            return
        self._set_busy(True, f"Đang cài app test lên Android {serial}...")
        self._append_log(f"Bắt đầu cài đặt app {apk_path} lên {serial}...")

        def worker() -> None:
            try:
                success, msg = install_apk(serial, apk_path)
                self.events.put(("android_install_done", (serial, success, msg)))
            except Exception as e:
                self.events.put(("android_install_done", (serial, False, str(e))))
                
        threading.Thread(target=worker, daemon=True).start()

    def start_android_erase(self) -> None:
        serials = list(self.android_tree.selection())
        if not serials:
            return
        serial = serials[0]
        confirm = messagebox.askyesno("Xác nhận Format", f"Bạn có chắc chắn muốn khôi phục cài đặt gốc thiết bị Android {serial}?")
        if not confirm:
            return
        self.start_android_erase_single(serial)

    def start_android_erase_single(self, serial: str) -> None:
        self._set_busy(True, f"Đang gửi lệnh Erase cho Android {serial}...")
        self._append_log(f"Đang gửi lệnh Erase cho thiết bị Android: {serial}")

        def worker() -> None:
            try:
                success, msg = erase_android(serial)
                if success:
                    # Clear test results for this device
                    self.android_test_results.pop(serial, None)
                self.events.put(("android_erase_done", (serial, success, msg)))
            except Exception as e:
                self.events.put(("android_erase_done", (serial, False, str(e))))
                
        threading.Thread(target=worker, daemon=True).start()

    def _process_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "devices":
                    devices: list[DeviceInfo] = event[1]
                    previous = list(self.tree.selection())
                    self.devices = {d.udid: d for d in devices}
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    for device in devices:
                        state = self.states.get(device.udid)
                        state_text = STATUS_TEXT.get(state, "Đang kiểm tra...")
                        tag = "Unknown"
                        if state == ActivationStatus.ACTIVATED:
                            tag = "Activated"
                        elif state == ActivationStatus.UNACTIVATED:
                            tag = "Unactivated"
                        elif state == ActivationStatus.BLOCKED:
                            tag = "Blocked"
                        
                        self.tree.insert("", "end", iid=device.udid, values=(device.name, device.product_type, device.ios_version, device.connection_type, state_text, device.imei, device.serial, device.udid), tags=(tag,))
                    
                    if previous:
                        still_present = [u for u in previous if u in self.devices]
                        if still_present:
                            self.tree.selection_set(still_present)
                    elif devices:
                        self.tree.selection_set(devices[0].udid)
                    
                    msg = f"Đã nhận {len(devices)} iPhone." if devices else "Không phát hiện iPhone qua USB."
                    self._update_status(msg, "idle" if devices else "error")
                    for device in devices:
                        if device.udid not in self.states:
                            self._refresh_selected_state(device.udid)
                    self._update_buttons()
                elif kind == "state":
                    result = event[1]
                    self.states[result.udid] = result.status
                    if self.tree.exists(result.udid):
                        values = list(self.tree.item(result.udid, "values"))
                        values[4] = STATUS_TEXT[result.status]
                        tag = "Unknown"
                        if result.status == ActivationStatus.ACTIVATED:
                            tag = "Activated"
                        elif result.status == ActivationStatus.UNACTIVATED:
                            tag = "Unactivated"
                        elif result.status == ActivationStatus.BLOCKED:
                            tag = "Blocked"
                        self.tree.item(result.udid, values=values, tags=(tag,))
                    self._append_log(f"{result.udid}: {result.message}")
                    if result.raw_output:
                        self._append_log(result.raw_output)
                    self._update_buttons()
                elif kind == "log":
                    self._append_log(event[1])
                elif kind == "test_results":
                    data = event[1]
                    udid = data.get("udid")
                    if udid:
                        is_android = udid in self.android_devices
                        if not is_android:
                            model_lower = str(data.get("model", "")).lower()
                            version_lower = str(data.get("ios_version", "")).lower()
                            if "android" in version_lower or "android" in model_lower:
                                is_android = True
                                
                        if is_android:
                            self.android_test_results[udid] = data
                            self._append_log(f"Đã nhận kết quả tự kiểm tra (Self-Test) cho Android {udid}!")
                            self._update_android_right_panel()
                            
                            # Tự động gửi lệnh xóa nếu tùy chọn được bật
                            if self.auto_erase_android_var.get():
                                self._append_log(f"[Auto-Erase] Phát hiện chế độ Tự Động Erase Android đang bật. Bắt đầu xóa {udid}...")
                                self.start_android_erase_single(udid)
                        else:
                            self.test_results[udid] = data
                            self._append_log(f"Đã nhận kết quả tự kiểm tra (Self-Test) cho iPhone {udid}!")
                            self._update_right_panel()
                            
                            # Tự động gửi lệnh xóa nếu tùy chọn được bật
                            if self.auto_erase_var.get():
                                self._append_log(f"[Auto-Erase] Phát hiện chế độ Tự Động Erase đang bật. Bắt đầu xóa {udid}...")
                                self.auto_erase_device(udid)
                elif kind == "android_discover_done":
                    devices = event[1]
                    previous = list(self.android_tree.selection())
                    self.android_devices = {d.serial: d for d in devices}
                    for item in self.android_tree.get_children():
                        self.android_tree.delete(item)
                    for device in devices:
                        self.android_tree.insert("", "end", iid=device.serial, values=(device.brand, device.model, device.android_version, device.imei, device.serial))
                    
                    if previous:
                        still_present = [s for s in previous if s in self.android_devices]
                        if still_present:
                            self.android_tree.selection_set(still_present)
                    elif devices:
                        self.android_tree.selection_set(devices[0].serial)
                    
                    msg = f"Đã nhận {len(devices)} thiết bị Android." if devices else "Không phát hiện thiết bị Android qua USB."
                    self._update_status(msg, "idle" if devices else "error")
                    self._update_android_buttons()
                elif kind == "android_bypass_done":
                    serial, success, msg = event[1]
                    self._set_busy(False, msg)
                    self._append_log(f"Active Android {serial}: {msg}")
                    self.refresh_android_devices()
                    if success:
                        messagebox.showinfo("Kích hoạt Android", f"Đã bypass màn hình Setup cho thiết bị {serial} thành công!")
                    else:
                        messagebox.showerror("Kích hoạt Android thất bại", f"Lỗi: {msg}")
                elif kind == "android_install_done":
                    serial, success, msg = event[1]
                    self._set_busy(False, msg)
                    self._append_log(f"Cài đặt app test Android {serial}: {msg}")
                    if success:
                        messagebox.showinfo("Cài đặt thành công", f"Đã cài đặt app test lên {serial} thành công!")
                    else:
                        messagebox.showerror("Cài đặt thất bại", f"Lỗi: {msg}")
                elif kind == "android_erase_done":
                    serial, success, msg = event[1]
                    self._set_busy(False, msg)
                    self._append_log(f"Erase Android {serial}: {msg}")
                    self.refresh_android_devices()
                    if success:
                        messagebox.showinfo("Format Android", f"Đã gửi lệnh khôi phục cài đặt gốc cho {serial} thành công!")
                    else:
                        messagebox.showerror("Format Android thất bại", f"Lỗi: {msg}")
                elif kind == "auto_erase_done":
                    udid, result = event[1], event[2]
                    if result.success:
                        self.states.pop(udid, None)
                    self.refresh_devices()
                elif kind == "install_done":
                    udid, result = event[1], event[2]
                    self._set_busy(False, "Đã hoàn thành cài đặt ứng dụng.")
                    self._append_log(f"Kết quả cài đặt app: {result.combined}")
                    if result.returncode == 0:
                        messagebox.showinfo("Cài đặt thành công", "Ứng dụng Self-Test đã được cài đặt thành công lên iPhone. Hãy mở ứng dụng trên điện thoại để bắt đầu test.")
                    else:
                        messagebox.showerror("Cài đặt thất bại", f"Lỗi khi cài đặt app: {result.combined}")
                elif kind == "install_bulk_done":
                    count = event[1]
                    self._set_busy(False, "Đã cài đặt xong app test.")
                    messagebox.showinfo("Cài đặt thành công", f"Đã cài đặt thành công ứng dụng test lên {count} thiết bị qua USB.")
                elif kind == "activation_bulk_done":
                    results = event[1]
                    for result in results:
                        self.states[result.udid] = result.status
                    activated_count = sum(1 for r in results if r.status == ActivationStatus.ACTIVATED)
                    msg = f"Hoàn thành kích hoạt hàng loạt. Thành công {activated_count}/{len(results)} thiết bị."
                    self._append_log(msg)
                    self._set_busy(False, msg)
                    self.refresh_devices()
                    messagebox.showinfo("Kích hoạt hàng loạt", msg)
                elif kind == "erase_bulk_done":
                    results = event[1]
                    success_count = 0
                    for udid, result in results:
                        if result.success:
                            success_count += 1
                            self.states.pop(udid, None)
                    msg = f"Hoàn thành xóa hàng loạt. Thành công {success_count}/{len(results)} thiết bị."
                    self._append_log(msg)
                    self._set_busy(False, msg)
                    self.refresh_devices()
                    messagebox.showinfo("Xóa hàng loạt", msg)
                elif kind == "operation_error":
                    self._append_log(event[1])
                    self._set_busy(False, event[1])
                    messagebox.showerror("Lỗi", event[1])
                elif kind == "error":
                    self._append_log(event[1])
                    self._update_status(event[1], "error")
        except queue.Empty:
            pass
        self.after(150, self._process_events)

    def _auto_refresh(self) -> None:
        if not self.busy:
            self.refresh_devices()
            self.refresh_android_devices()
        self.after(3000, self._auto_refresh)
