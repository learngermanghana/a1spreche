import Foundation
import SwiftUI

// What we keep in Keychain
struct TokenPair: Codable {
    let accessToken: String
    let refreshToken: String
    let expiry: Date
}

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var errorMessage: String?

    private let accountKey = "falowen.tokenpair"
    private var bootstrapping = false

    func bootstrap() async {
        await ProtectedData.waitIfNeeded()
        if bootstrapping { return }
        bootstrapping = true
        defer { bootstrapping = false }

        do {
            // 1) No saved session → show login, but don’t call logout
            guard let pair: TokenPair = try Keychain.shared.readCodable(TokenPair.self, account: accountKey) else {
                isAuthenticated = false
                errorMessage = nil
                return
            }

            // 2) We have a session → stay signed in by default
            isAuthenticated = true
            errorMessage = nil

            // 3) Refresh only if near/after expiry (tweak the grace as you like)
            let needsRefresh = pair.expiry <= Date().addingTimeInterval(60) // 60s grace
            guard needsRefresh else { return }

            do {
                let newPair = try await AuthAPI.refresh(using: pair.refreshToken)
                try Keychain.shared.saveCodable(newPair, account: accountKey)
                #if DEBUG
                print("♻️ Refreshed token. New expiry:", newPair.expiry)
                #endif
            } catch let api as AuthAPIError {
                switch api {
                case .http(let code) where code == 401:
                    // Only a true 401 on refresh ends the session.
                    try? Keychain.shared.delete(account: accountKey)
                    isAuthenticated = false
                    errorMessage = "Session expired. Please sign in again."
                default:
                    // Network/timeout/5xx/JSON hiccups → stay logged in; try again later.
                    #if DEBUG
                    print("⚠️ Refresh failed (transient):", api.localizedDescription)
                    #endif
                }
            } catch {
                // Any other error → treat as transient; keep user signed in.
                #if DEBUG
                print("⚠️ Refresh failed (other):", error.localizedDescription)
                #endif
            }
        } catch {
            // Rare Keychain read error
            #if DEBUG
            print("‼️ Bootstrap Keychain error:", error.localizedDescription)
            #endif
            isAuthenticated = false
            errorMessage = error.localizedDescription
        }
    }

    // keep your existing login(...) and logout() or use the versions we added earlier
}


    // Sign out
    func logout() {
        do {
            try Keychain.shared.delete(account: accountKey)
        } catch {
            errorMessage = error.localizedDescription
            #if DEBUG
            print("⚠️ Logout keychain error:", error.localizedDescription)
            #endif
        }
        isAuthenticated = false
    }

    // Attach Bearer to requests (optional helper)
    func authorizedRequest(url: URL) throws -> URLRequest {
        guard let pair: TokenPair = try Keychain.shared.readCodable(TokenPair.self, account: accountKey)
        else { throw URLError(.userAuthenticationRequired) }
        var req = URLRequest(url: url)
        req.addValue("Bearer \(pair.accessToken)", forHTTPHeaderField: "Authorization")
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        return req
    }
}

