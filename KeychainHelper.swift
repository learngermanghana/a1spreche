import Security

enum KeychainKey: String {
    case accessToken
    case refreshToken
}

private let service = "com.yourbundle.yourapp.auth" // <- namespace your items

@discardableResult
func saveToken(_ token: String, key: KeychainKey) -> OSStatus {
    let data = Data(token.utf8)

    // Base attributes that identify the item
    let baseQuery: [String: Any] = [
        kSecClass as String           : kSecClassGenericPassword,
        kSecAttrService as String     : service,
        kSecAttrAccount as String     : key.rawValue,
        // If you share across apps/targets, also set kSecAttrAccessGroup
        // kSecAttrAccessGroup as String : "YOUR_TEAM_ID.com.your.group"
    ]

    // Try an update first
    let updateAttrs: [String: Any] = [
        kSecValueData as String       : data,
        // Keep accessibility consistent across add/update:
        kSecAttrAccessible as String  : kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    ]

    let updateStatus = SecItemUpdate(baseQuery as CFDictionary, updateAttrs as CFDictionary)
    if updateStatus == errSecSuccess { return updateStatus }
    if updateStatus != errSecItemNotFound { return updateStatus }

    // If not found, add it
    var addQuery = baseQuery
    addQuery[kSecValueData as String]      = data
    addQuery[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    // If you use iCloud Keychain, decide explicitly:
    // addQuery[kSecAttrSynchronizable as String] = kCFBooleanFalse!

    return SecItemAdd(addQuery as CFDictionary, nil)
}

func loadToken(key: KeychainKey) -> String? {
    let query: [String: Any] = [
        kSecClass as String           : kSecClassGenericPassword,
        kSecAttrService as String     : service,
        kSecAttrAccount as String     : key.rawValue,
        kSecReturnData as String      : kCFBooleanTrue!,
        kSecMatchLimit as String      : kSecMatchLimitOne,
        // If you ever stored synchronizable, include this to match them too:
        // kSecAttrSynchronizable as String : kSecAttrSynchronizableAny
    ]
    var item: AnyObject?
    guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
          let data = item as? Data,
          let token = String(data: data, encoding: .utf8) else {
        return nil
    }
    return token
}

@discardableResult
func deleteToken(for key: KeychainKey) -> OSStatus {
    var query: [String: Any] = [
        kSecClass as String           : kSecClassGenericPassword,
        kSecAttrService as String     : service,
        kSecAttrAccount as String     : key.rawValue
    ]
    // If you might have created synchronizable items, include this to delete those too:
    // query[kSecAttrSynchronizable as String] = kSecAttrSynchronizableAny
    return SecItemDelete(query as CFDictionary)
}
