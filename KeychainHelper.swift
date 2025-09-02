import Foundation
import Security

// Keys used for storing tokens in the Keychain.
enum KeychainKey: String {
    case accessToken
    case refreshToken
}

/// Save a token into the Keychain under the provided key.
/// Existing values for the key are overwritten.
func saveToken(_ token: String, key: KeychainKey) {
    guard let data = token.data(using: .utf8) else { return }
    let baseQuery: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: key.rawValue
    ]
    // Remove any existing entry before adding a new one
    SecItemDelete(baseQuery as CFDictionary)
    var addQuery = baseQuery
    addQuery[kSecValueData as String] = data
    SecItemAdd(addQuery as CFDictionary, nil)
}

/// Retrieve a token from the Keychain.
/// - Returns: The token if it exists, otherwise ``nil``.
func loadToken(for key: KeychainKey) -> String? {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: key.rawValue,
        kSecReturnData as String: true,
        kSecMatchLimit as String: kSecMatchLimitOne,
    ]

    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecSuccess,
       let data = item as? Data,
       let token = String(data: data, encoding: .utf8) {
        return token
    }
    return nil
}

/// Delete a token stored under the provided key.
func deleteToken(for key: KeychainKey) {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: key.rawValue
    ]
    SecItemDelete(query as CFDictionary)
}
