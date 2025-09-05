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

    private var bootstrapping = false

    func bootstrap() async {
        await ProtectedData.waitIfNeeded()
        if bootstrapping { return }
        bootstrapping = true
        defer { bootstrapping = false }

        do {
            var pair = try await TokenStore.shared.currentPair()
            isAuthenticated = true
            errorMessage = nil

            let needsRefresh = pair.expiry <= Date().addingTimeInterval(60)
            guard needsRefresh else { return }

            do {
                pair = try await TokenStore.shared.ensureFreshPair()
                try await TokenStore.shared.save(pair)
                #if DEBUG
                print("♻️ Refreshed token. New expiry:", pair.expiry)
                #endif
            } catch let api as AuthAPIError {
                switch api {
                case .http(let code) where code == 401:
                    try? await TokenStore.shared.clear()
                    isAuthenticated = false
                    errorMessage = "Session expired. Please sign in again."
                default:
                    #if DEBUG
                    print("⚠️ Refresh failed (transient):", api.localizedDescription)
                    #endif
                }
            } catch {
                #if DEBUG
                print("⚠️ Refresh failed (other):", error.localizedDescription)
                #endif
            }
        } catch {
            #if DEBUG
            print("‼️ Bootstrap token error:", error.localizedDescription)
            #endif
            isAuthenticated = false
            errorMessage = nil
        }
    }

    func login(email: String, password: String) async {
        do {
            let pair = try await AuthAPI.login(email: email, password: password)
            try await TokenStore.shared.save(pair)
            isAuthenticated = true
            errorMessage = nil
        } catch let api as AuthAPIError {
            isAuthenticated = false
            errorMessage = api.localizedDescription
        } catch {
            isAuthenticated = false
            errorMessage = error.localizedDescription
        }
    }

    func logout() async {
        do {
            try await TokenStore.shared.clear()
        } catch {
            errorMessage = error.localizedDescription
            #if DEBUG
            print("⚠️ Logout token error:", error.localizedDescription)
            #endif
        }
        isAuthenticated = false
    }

    func authorizedRequest(url: URL) async throws -> URLRequest {
        let pair = try await TokenStore.shared.currentPair()
        var req = URLRequest(url: url)
        req.addValue("Bearer \(pair.accessToken)", forHTTPHeaderField: "Authorization")
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        return req
    }
}

