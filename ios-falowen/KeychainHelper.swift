import Foundation
import Security

struct KeychainError: LocalizedError {
    let status: OSStatus
    var errorDescription: String? {
        SecCopyErrorMessageString(status, nil) as String? ?? "Keychain error \(status)"
    }
}

final class Keychain {
    static let shared = Keychain()
    private init() {}

    // Namespace for your app’s items (stable across builds)
    // If you already shipped with "com.falowen.app" and want to keep it, hardcode that string.
    private let service = Bundle.main.bundleIdentifier ?? "com.falowen.app"

    // Choose accessibility that fits your needs:
    // - kSecAttrAccessibleAfterFirstUnlock            → persists and is restorable via encrypted backups
    // - kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly → persists but NOT restored to other devices
    private let accessibility: CFString = kSecAttrAccessibleAfterFirstUnlock

    // Save raw Data (overwrites existing for same account)
    func save(_ data: Data, account: String) throws {
        var base: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecAttrAccessible as String: accessibility
        ]

        // Remove any existing item first, then add the new one.
        SecItemDelete(base as CFDictionary)

        base[kSecValueData as String] = data
        let status = SecItemAdd(base as CFDictionary, nil)
        guard status == errSecSuccess else { throw KeychainError(status: status) }
    }

    // Read raw Data
    func read(account: String) throws -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)

        if status == errSecItemNotFound {
            return nil
        } else if status == errSecSuccess {
            return item as? Data
        } else {
            throw KeychainError(status: status)
        }
    }

    // Delete one item
    func delete(account: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError(status: status)
        }
    }

    // Codable helpers
    func saveCodable<T: Codable>(_ value: T, account: String) throws {
        let data = try JSONEncoder().encode(value)
        try save(data, account: account)
    }

    func readCodable<T: Codable>(_ type: T.Type, account: String) throws -> T? {
        guard let data = try read(account: account) else { return nil }
        return try JSONDecoder().decode(type, from: data)
    }
}

