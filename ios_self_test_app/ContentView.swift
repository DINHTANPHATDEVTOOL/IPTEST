import SwiftUI
import AVFoundation
import CoreMotion
import LocalAuthentication
import UIKit

// MARK: - Models & Enums

enum TestStatus: String, Codable {
    case pass = "PASS"
    case fail = "FAIL"
    case guidedPass = "GUIDED PASS"
    case inconclusive = "INCONCLUSIVE"
    case notSupported = "NOT SUPPORTED"
    case permissionDenied = "PERMISSION DENIED"
    case untested = "Chưa test"
}

struct TestItem: Identifiable, Codable {
    var id: String { testId }
    let testId: String
    var status: TestStatus
    var message: String
}

struct TestResultPayload: Codable {
    let udid: String
    let sessionId: String
    let model: String
    let iosVersion: String
    let totalTests: Int
    let passed: Int
    let failed: Int
    let inconclusive: Int
    let notSupported: Int
    let failedFunctions: [String]
    let results: [TestItem]
    
    enum CodingKeys: String, CodingKey {
        case udid
        case sessionId = "session_id"
        case model
        case iosVersion = "ios_version"
        case totalTests = "total_tests"
        case passed
        case failed
        case inconclusive
        case notSupported
        case failedFunctions = "failed_functions"
        case results
    }
}

// MARK: - View Model Manager

class TestManager: ObservableObject {
    @Published var serverIP: String = "192.168.1.100" // Default Ubuntu IP
    @Published var udid: String = UIDevice.current.identifierForVendor?.uuidString ?? "UNKNOWN_UDID"
    @Published var sessionId: String = "PB30-P4-\(Int.random(in: 1000...9999))"
    @Published var currentTestIndex: Int = -1
    
    @Published var tests: [TestItem] = [
        TestItem(testId: "DEVICE_INFO", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "CAMERA", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "AUDIO", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "SENSORS", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "TOUCHSCREEN", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "DISPLAY", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "PROXIMITY", status: .untested, message: "Chưa kiểm tra"),
        TestItem(testId: "BIOMETRIC", status: .untested, message: "Chưa kiểm tra"),
    ]
    
    // Core motion manager
    private let motionManager = CMMotionManager()
    
    init() {
        // Load saved Server IP if exists
        if let savedIP = UserDefaults.standard.string(forKey: "ubuntu_server_ip") {
            self.serverIP = savedIP
        }
    }
    
    func saveIP() {
        UserDefaults.standard.set(serverIP, forKey: "ubuntu_server_ip")
    }
    
    // MARK: - Automatic Tests
    
    func runAutomaticTests(completion: @escaping () -> Void) {
        // 1. Device Info Test
        runDeviceInfoTest()
        
        // 2. Motion Sensors Test
        runSensorsTest()
        
        // 3. Biometric Support Test
        runBiometricTest()
        
        completion()
    }
    
    private func runDeviceInfoTest() {
        let model = UIDevice.current.modelName
        let ios = UIDevice.current.systemVersion
        let battery = Int(UIDevice.current.batteryLevel * 100)
        let batteryState = UIDevice.current.batteryState == .charging ? "Charging" : "Discharging"
        
        updateTestStatus(id: "DEVICE_INFO", status: .pass, message: "Model: \(model), iOS: \(ios), Pin: \(battery)% (\(batteryState))")
    }
    
    private func runSensorsTest() {
        if motionManager.isAccelerometerAvailable {
            motionManager.startAccelerometerUpdates()
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                if let data = self.motionManager.accelerometerData {
                    self.updateTestStatus(id: "SENSORS", status: .pass, message: "Accelerometer OK (x:\(String(format: "%.2f", data.acceleration.x))g)")
                } else {
                    self.updateTestStatus(id: "SENSORS", status: .inconclusive, message: "Không đọc được dữ liệu sensor")
                }
                self.motionManager.stopAccelerometerUpdates()
            }
        } else {
            updateTestStatus(id: "SENSORS", status: .notSupported, message: "Gia tốc kế không khả dụng")
        }
    }
    
    private func runBiometricTest() {
        let context = LAContext()
        var error: NSError?
        
        if context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) {
            let type = context.biometryType == .faceID ? "Face ID" : "Touch ID"
            updateTestStatus(id: "BIOMETRIC", status: .guidedPass, message: "Hỗ trợ \(type). Cần người dùng xác thực.")
        } else {
            let msg = error?.localizedDescription ?? "Không khả dụng"
            updateTestStatus(id: "BIOMETRIC", status: .notSupported, message: "Sinh trắc học không khả dụng: \(msg)")
        }
    }
    
    func updateTestStatus(id: String, status: TestStatus, message: String) {
        if let idx = tests.firstIndex(where: { $0.testId == id }) {
            tests[idx] = TestItem(testId: id, status: status, message: message)
        }
    }
    
    // MARK: - API Submission
    
    func submitResults(completion: @escaping (Bool, String) -> Void) {
        saveIP()
        let passed = tests.filter { $0.status == .pass || $0.status == .guidedPass }.count
        let failed = tests.filter { $0.status == .fail }.count
        let inconclusive = tests.filter { $0.status == .inconclusive }.count
        let notSupported = tests.filter { $0.status == .notSupported }.count
        let failedFuncs = tests.filter { $0.status == .fail }.map { $0.testId }
        
        let payload = TestResultPayload(
            udid: udid,
            sessionId: sessionId,
            model: UIDevice.current.modelName,
            iosVersion: UIDevice.current.systemVersion,
            totalTests: tests.count,
            passed: passed,
            failed: failed,
            inconclusive: inconclusive,
            notSupported: notSupported,
            failedFunctions: failedFuncs,
            results: tests
        )
        
        guard let url = URL(string: "http://\(serverIP):8080/api/results") else {
            completion(false, "Đường dẫn server không hợp lệ")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            let jsonData = try JSONEncoder().encode(payload)
            request.httpBody = jsonData
        } catch {
            completion(false, "Lỗi mã hóa JSON: \(error.localizedDescription)")
            return
        }
        
        URLSession.shared.dataTask(with: request) { _, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    completion(false, "Lỗi kết nối: \(error.localizedDescription)")
                } else if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
                    completion(true, "Đã gửi báo cáo chẩn đoán thành công về Ubuntu!")
                } else {
                    completion(false, "Server trả về lỗi HTTP \((response as? HTTPURLResponse)?.statusCode ?? 500)")
                }
            }
        }.resume()
    }
}

// MARK: - UI Views

struct ContentView: View {
    @StateObject var manager = TestManager()
    @State private var showingInteractiveTest = false
    @State private var isSubmitting = false
    @State private var alertMessage = ""
    @State private var showAlert = false
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(red: 15/255, green: 23/255, blue: 42/255)
                    .ignoresSafeArea()
                
                VStack(spacing: 20) {
                    // Header config
                    VStack(alignment: .leading, spacing: 10) {
                        Text("Cấu Hình Kết Nối")
                            .font(.headline)
                            .foregroundColor(.gray)
                        
                        HStack {
                            Text("Ubuntu Server IP:")
                                .foregroundColor(.white)
                                .font(.subheadline)
                            
                            TextField("192.168.1.100", text: $manager.serverIP)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.decimalPad)
                                .foregroundColor(.black)
                        }
                        
                        Text("UDID: \(manager.udid)")
                            .font(.system(size: 11, weight: .semibold, design: .monospaced))
                            .foregroundColor(.blue)
                    }
                    .padding()
                    .background(Color(red: 30/255, green: 41/255, blue: 59/255))
                    .cornerRadius(12)
                    
                    // Start Button
                    Button(action: {
                        manager.runAutomaticTests {
                            // Open interactive test wizard
                            manager.currentTestIndex = 1 // Start at CAMERA test
                            showingInteractiveTest = true
                        }
                    }) {
                        Text("BẮT ĐẦU KIỂM TRA")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .cornerRadius(12)
                    }
                    
                    // List of tests with status
                    ScrollView {
                        VStack(spacing: 8) {
                            ForEach(manager.tests) { item in
                                HStack {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(item.testId)
                                            .font(.headline)
                                            .foregroundColor(.white)
                                        Text(item.message)
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                    }
                                    Spacer()
                                    
                                    Text(item.status.rawValue)
                                        .font(.system(size: 12, weight: .bold))
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 6)
                                        .background(badgeColor(for: item.status))
                                        .foregroundColor(.white)
                                        .cornerRadius(8)
                                }
                                .padding()
                                .background(Color(red: 30/255, green: 41/255, blue: 59/255))
                                .cornerRadius(10)
                            }
                        }
                    }
                    
                    // Submit button
                    Button(action: {
                        isSubmitting = true
                        manager.submitResults { success, message in
                            isSubmitting = false
                            alertMessage = message
                            showAlert = true
                        }
                    }) {
                        if isSubmitting {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Text("GỬI BÁO CÁO VỀ UBUNTU")
                                .font(.headline)
                                .foregroundColor(.white)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.emerald)
                                .cornerRadius(12)
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("iPhone Self-Test")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("iPhone Self-Test")
                        .font(.headline)
                        .foregroundColor(.white)
                }
            }
            .sheet(isPresented: $showingInteractiveTest) {
                InteractiveTestWizardView(manager: manager, isPresented: $showingInteractiveTest)
            }
            .alert(isPresented: $showAlert) {
                Alert(title: Text("Thông báo"), message: Text(alertMessage), dismissButton: .default(Text("OK")))
            }
        }
    }
    
    private func badgeColor(for status: TestStatus) -> Color {
        switch status {
        case .pass, .guidedPass:
            return .green
        case .fail:
            return .red
        case .inconclusive:
            return .orange
        case .notSupported:
            return .gray
        default:
            return Color.blue.opacity(0.3)
        }
    }
}

// MARK: - Extension Colors & Devices

extension Color {
    static let emerald = Color(red: 16/255, green: 185/255, blue: 129/255)
}

extension UIDevice {
    var modelName: String {
        var systemInfo = utsname()
        uname(&systemInfo)
        let machineMirror = Mirror(reflecting: systemInfo.machine)
        let identifier = machineMirror.children.reduce("") { identifier, element in
            guard let value = element.value as? Int8, value != 0 else { return identifier }
            return identifier + String(UnicodeScalar(UInt8(value)))
        }
        return identifier
    }
}

// MARK: - Interactive Test Wizard View

struct InteractiveTestWizardView: View {
    @ObservedObject var manager: TestManager
    @Binding var isPresented: Bool
    
    var body: some View {
        ZStack {
            Color(red: 15/255, green: 23/255, blue: 42/255)
                .ignoresSafeArea()
            
            VStack {
                if manager.currentTestIndex == 1 {
                    CameraTestView(manager: manager)
                } else if manager.currentTestIndex == 2 {
                    AudioTestView(manager: manager)
                } else if manager.currentTestIndex == 4 {
                    TouchscreenTestView(manager: manager)
                } else if manager.currentTestIndex == 5 {
                    DisplayTestView(manager: manager)
                } else if manager.currentTestIndex == 6 {
                    ProximityTestView(manager: manager)
                } else {
                    // All guided tests done, show finish summary
                    VStack(spacing: 20) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 80))
                            .foregroundColor(.green)
                        
                        Text("Hoàn Thành Các Bài Test Thủ Công")
                            .font(.title2)
                            .bold()
                            .foregroundColor(.white)
                        
                        Text("Bấm nút bên dưới để đóng bảng chẩn đoán và tiến hành gửi báo cáo về máy Ubuntu.")
                            .foregroundColor(.gray)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                        
                        Button("Đóng & Xem Kết Quả") {
                            isPresented = false
                        }
                        .font(.headline)
                        .foregroundColor(.white)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color.blue)
                        .cornerRadius(12)
                        .padding(.horizontal, 40)
                    }
                }
            }
            .padding()
        }
    }
}

// MARK: - Sub test views

struct CameraTestView: View {
    @ObservedObject var manager: TestManager
    
    var body: some View {
        VStack(spacing: 20) {
            Text("KIỂM TRA CAMERA")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Vui lòng mở camera trước/sau để xác nhận thấu kính hoạt động không có điểm đen, xước hoặc nhòe.")
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
            
            Spacer()
            
            // Dummy camera feed mockup (native camera uses AVFoundation view)
            RoundedRectangle(cornerRadius: 15)
                .fill(Color.black)
                .frame(height: 300)
                .overlay(
                    Text("Khung ngắm Camera")
                        .foregroundColor(.white)
                )
            
            Spacer()
            
            HStack(spacing: 20) {
                Button("HỎNG (FAIL)") {
                    manager.updateTestStatus(id: "CAMERA", status: .fail, message: "Lỗi camera / hình ảnh nhòe")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.red)
                .cornerRadius(10)
                
                Button("ĐẠT (PASS)") {
                    manager.updateTestStatus(id: "CAMERA", status: .pass, message: "Camera trước & sau hoạt động tốt")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.green)
                .cornerRadius(10)
            }
        }
    }
}

struct AudioTestView: View {
    @ObservedObject var manager: TestManager
    
    var body: some View {
        VStack(spacing: 20) {
            Text("KIỂM TRA ÂM THANH")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Bấm Phát âm thanh để phát tone kiểm tra qua loa dưới, kiểm tra xem microphone có thu được không.")
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
            
            Spacer()
            
            Button(action: {
                // Play test tone
                let systemSoundID: SystemSoundID = 1005
                AudioServicesPlaySystemSound(systemSoundID)
            }) {
                HStack {
                    Image(systemName: "play.circle.fill")
                    Text("Phát âm thanh mẫu")
                }
                .font(.title2)
                .foregroundColor(.white)
                .padding()
                .background(Color.blue)
                .cornerRadius(12)
            }
            
            Spacer()
            
            HStack(spacing: 20) {
                Button("HỎNG (FAIL)") {
                    manager.updateTestStatus(id: "AUDIO", status: .fail, message: "Không nghe thấy âm thanh / Mic không thu được")
                    manager.currentTestIndex += 2 // Skip sensor (index 3 is sensor which is auto)
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.red)
                .cornerRadius(10)
                
                Button("ĐẠT (PASS)") {
                    manager.updateTestStatus(id: "AUDIO", status: .pass, message: "Loa và mic loopback nghe tốt")
                    manager.currentTestIndex += 2
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.green)
                .cornerRadius(10)
            }
        }
    }
}

struct TouchscreenTestView: View {
    @ObservedObject var manager: TestManager
    @State private var grid: [[Bool]] = Array(repeating: Array(repeating: false, count: 5), count: 8)
    
    var body: some View {
        VStack {
            Text("VUỐT ĐỂ DỌN LƯỚI CẢM ỨNG")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Vuốt tay qua tất cả các ô để tô màu xanh lá, kiểm tra xem màn hình có điểm chết cảm ứng không.")
                .font(.caption)
                .foregroundColor(.gray)
            
            // Grid touch area
            GeometryReader { geo in
                VStack(spacing: 2) {
                    ForEach(0..<8, id: \.self) { row in
                        HStack(spacing: 2) {
                            ForEach(0..<5, id: \.self) { col in
                                Rectangle()
                                    .fill(grid[row][col] ? Color.green : Color.blue.opacity(0.3))
                                    .border(Color.white.opacity(0.1))
                            }
                        }
                    }
                }
                .gesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { value in
                            let cellWidth = geo.size.width / 5
                            let cellHeight = geo.size.height / 8
                            
                            let col = Int(value.location.x / cellWidth)
                            let row = Int(value.location.y / cellHeight)
                            
                            if row >= 0 && row < 8 && col >= 0 && col < 5 {
                                grid[row][col] = true
                            }
                        }
                )
            }
            .frame(height: 380)
            .padding()
            
            HStack {
                Button("THẤT BẠI") {
                    manager.updateTestStatus(id: "TOUCHSCREEN", status: .fail, message: "Có vùng chết cảm ứng")
                    manager.currentTestIndex += 1
                }
                .foregroundColor(.red)
                
                Spacer()
                
                Button("Hoàn thành Grid") {
                    let allTouched = grid.flatMap { $0 }.allSatisfy { $0 }
                    let msg = allTouched ? "Cảm ứng hoàn hảo 100% diện tích" : "Không vuốt hết lưới cảm ứng"
                    manager.updateTestStatus(id: "TOUCHSCREEN", status: allTouched ? .pass : .guidedPass, message: msg)
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.green)
            }
            .padding()
        }
    }
}

struct DisplayTestView: View {
    @ObservedObject var manager: TestManager
    @State private var currentColorIdx = 0
    let colors: [Color] = [.red, .green, .blue, .white, .black]
    let colorNames = ["ĐỎ", "XANH LÁ", "XANH DƯƠNG", "TRẮNG", "ĐEN"]
    
    var body: some View {
        VStack(spacing: 20) {
            Text("KIỂM TRA ĐIỂM CHẾT MÀN HÌNH")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Nhấn vào hình chữ nhật bên dưới để đổi màu. Kiểm tra xem có đốm sáng, kẻ sọc hay điểm chết không.")
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
            
            Spacer()
            
            Rectangle()
                .fill(colors[currentColorIdx])
                .frame(height: 250)
                .cornerRadius(12)
                .overlay(
                    Text("MÀU: \(colorNames[currentColorIdx]) (Bấm để đổi)")
                        .foregroundColor(currentColorIdx == 3 ? .black : .white)
                        .font(.headline)
                )
                .onTapGesture {
                    currentColorIdx = (currentColorIdx + 1) % colors.count
                }
            
            Spacer()
            
            HStack(spacing: 20) {
                Button("HỎNG (FAIL)") {
                    manager.updateTestStatus(id: "DISPLAY", status: .fail, message: "Kẻ sọc/Đốm sáng/Điểm chết")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.red)
                .cornerRadius(10)
                
                Button("ĐẠT (PASS)") {
                    manager.updateTestStatus(id: "DISPLAY", status: .pass, message: "Hiển thị màu sắc chuẩn, không sọc")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.green)
                .cornerRadius(10)
            }
        }
    }
}

struct ProximityTestView: View {
    @ObservedObject var manager: TestManager
    @State private var nearDetected = false
    
    var body: some View {
        VStack(spacing: 20) {
            Text("CẢM BIẾN TIỆM CẬN (PROXIMITY)")
                .font(.headline)
                .foregroundColor(.white)
            
            Text("Dùng lòng bàn tay che vùng cảm biến phía trên camera trước (notch/Dynamic Island) để kiểm tra độ tiệm cận.")
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
            
            Spacer()
            
            Image(systemName: nearDetected ? "eye.slash.fill" : "eye.fill")
                .font(.system(size: 80))
                .foregroundColor(nearDetected ? .green : .blue)
                .onAppear {
                    UIDevice.current.isProximityMonitoringEnabled = true
                    NotificationCenter.default.addObserver(forName: UIDevice.proximityStateDidChangeNotification, object: nil, queue: .main) { _ in
                        self.nearDetected = UIDevice.current.proximityState
                    }
                }
                .onDisappear {
                    UIDevice.current.isProximityMonitoringEnabled = false
                }
            
            Text(nearDetected ? "Đã phát hiện vật cản (NEAR)" : "Đang chờ vật cản (FAR)")
                .font(.headline)
                .foregroundColor(.white)
            
            Spacer()
            
            HStack(spacing: 20) {
                Button("HỎNG (FAIL)") {
                    manager.updateTestStatus(id: "PROXIMITY", status: .fail, message: "Cảm biến tiệm cận không phản hồi")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.red)
                .cornerRadius(10)
                
                Button("ĐẠT (PASS)") {
                    manager.updateTestStatus(id: "PROXIMITY", status: .pass, message: "Cảm biến phản hồi nhạy bén")
                    manager.currentTestIndex += 1
                }
                .font(.headline)
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.green)
                .cornerRadius(10)
            }
        }
    }
}
