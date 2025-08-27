import Security

enum KeychainKey: String {
    case accessToken
    case refreshToken
}

func saveToken(_ token: String, key: KeychainKey) {
    let data = Data(token.utf8)
    let query: [String: Any] = [
        kSecClass as String       : kSecClassGenericPassword,
        kSecAttrAccount as String : key.rawValue,
        kSecValueData as String   : data
    ]
    SecItemDelete(query as CFDictionary)              // overwrite if it exists
    SecItemAdd(query as CFDictionary, nil)
}

func loadToken(key: KeychainKey) -> String? {
    let query: [String: Any] = [
        kSecClass as String       : kSecClassGenericPassword,
        kSecAttrAccount as String : key.rawValue,
        kSecReturnData as String  : kCFBooleanTrue!,
        kSecMatchLimit as String  : kSecMatchLimitOne
    ]
    var item: AnyObject?
    guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
          let data = item as? Data,
          let token = String(data: data, encoding: .utf8)
    else { return nil }
    return token
}

func deleteToken(for key: KeychainKey) {
    let query: [String: Any] = [
        kSecClass as String       : kSecClassGenericPassword,
        kSecAttrAccount as String : key.rawValue
    ]
    SecItemDelete(query as CFDictionary)
}
