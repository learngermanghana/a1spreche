import UIKit

enum ProtectedData {
    /// Wait until protected data (Keychain) is available after reboot/unlock.
    static func waitIfNeeded() async {
        if UIApplication.shared.isProtectedDataAvailable { return }
        while !UIApplication.shared.isProtectedDataAvailable {
            try? await Task.sleep(nanoseconds: 200_000_000) // 200 ms
        }
    }
}

