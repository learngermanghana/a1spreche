import Foundation

// --- CONFIG ---
private let USE_STUB = false                           // true = stubbed tokens for testing persistence
private let BASE = URL(string: "https://www.falowen.app")!
// If your server is elsewhere, change BASE to e.g. https://api.falowen.app
private let PATH_LOGIN   = "/auth/login"               // change to "/api/auth/login" if needed
private let PATH_REFRESH = "/auth/refresh"             // change to "/api/auth/refresh" if needed

// Some backends expect refreshToken in snake_case or camelCase.
// Pick which one your server expects:
private enum RefreshParamStyle { case snake, camel }
private let REFRESH_STYLE: RefreshParamStyle = .snake
// ---------------

enum AuthAPIError: LocalizedError {
    case http(Int), badResponse, decodeError, network(String)
    var errorDescription: String? {
        switch self {
        case .http(let code):   return "Server error (\(code))"
        case .badResponse:      return "Invalid server response"
        case .decodeError:      return "Couldn’t decode server response"
        case .network(let msg): return msg
        }
    }
}

// Accept snake_case or camelCase and be tolerant about expiresIn type.
private struct LoginResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int

    private enum CodingKeys: String, CodingKey {
        case accessToken, refreshToken, expiresIn
        case access_token, refresh_token, expires_in
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)

        func decodeString(for keys: (CodingKeys, CodingKeys)) throws -> String {
            if let v = try c.decodeIfPresent(String.self, forKey: keys.0) { return v }
            if let v = try c.decodeIfPresent(String.self, forKey: keys.1) { return v }
            throw AuthAPIError.decodeError
        }

        func decodeIntLike(for keys: (CodingKeys, CodingKeys)) throws -> Int {
            if let v = try c.decodeIfPresent(Int.self, forKey: keys.0) { return v }
            if let v = try c.decodeIfPresent(Int.self, forKey: keys.1) { return v }
            if let s = try c.decodeIfPresent(String.self, forKey: keys.0), let v = Int(s) { return v }
            if let s = try c.decodeIfPresent(String.self, forKey: keys.1), let v = Int(s) { return v }
            if let d = try c.decodeIfPresent(Double.self, forKey: keys.0) { return Int(d) }
            if let d = try c.decodeIfPresent(Double.self, forKey: keys.1) { return Int(d) }
            throw AuthAPIError.decodeError
        }

        accessToken = try decodeString(for: (.accessToken, .access_token))
        refreshToken = try decodeString(for: (.refreshToken, .refresh_token))
        expiresIn = try decodeIntLike(for: (.expiresIn, .expires_in))
    }
}

enum AuthAPI {

    // MARK: Public

    static func login(email: String, password: String) async throws -> TokenPair {
        if USE_STUB {
            try await Task.sleep(nanoseconds: 300_000_000)
            return TokenPair(
                accessToken: "access_" + UUID().uuidString,
                refreshToken: "refresh_" + UUID().uuidString,
                expiry: Date().addingTimeInterval(60 * 60)
            )
        } else {
            return try await liveLogin(email: email, password: password)
        }
    }

    static func refresh(using refreshToken: String) async throws -> TokenPair {
        if USE_STUB {
            try await Task.sleep(nanoseconds: 200_000_000)
            return TokenPair(
                accessToken: "access_" + UUID().uuidString,
                refreshToken: refreshToken,
                expiry: Date().addingTimeInterval(60 * 60)
            )
        } else {
            return try await liveRefresh(using: refreshToken)
        }
    }

    // MARK: Live calls

    private static func liveLogin(email: String, password: String) async throws -> TokenPair {
        var req = URLRequest(url: BASE.appendingPathComponent(PATH_LOGIN))
        req.httpMethod = "POST"
        req.timeoutInterval = 15
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        req.httpBody = try JSONEncoder().encode(["email": email, "password": password])

        #if DEBUG
        print("LOGIN URL:", req.url?.absoluteString ?? "")
        #endif

        do {
            let (data, resp) = try await URLSession.shared.data(for: req)
            #if DEBUG
            if let body = String(data: data, encoding: .utf8) {
                print("LOGIN raw response:", body)
            }
            #endif
            guard let http = resp as? HTTPURLResponse else { throw AuthAPIError.badResponse }
            guard (200..<300).contains(http.statusCode) else { throw AuthAPIError.http(http.statusCode) }
            let lr = try JSONDecoder().decode(LoginResponse.self, from: data)
            return TokenPair(
                accessToken: lr.accessToken,
                refreshToken: lr.refreshToken,
                expiry: Date().addingTimeInterval(TimeInterval(lr.expiresIn))
            )
        } catch let e as URLError {
            throw AuthAPIError.network(e.localizedDescription)
        }
    }

    private static func liveRefresh(using refreshToken: String) async throws -> TokenPair {
        var req = URLRequest(url: BASE.appendingPathComponent(PATH_REFRESH))
        req.httpMethod = "POST"
        req.timeoutInterval = 15
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        req.addValue("application/json", forHTTPHeaderField: "Accept")

        switch REFRESH_STYLE {
        case .snake:
            req.httpBody = try JSONEncoder().encode(["refresh_token": refreshToken])
        case .camel:
            req.httpBody = try JSONEncoder().encode(["refreshToken": refreshToken])
        }

        #if DEBUG
        print("REFRESH URL:", req.url?.absoluteString ?? "")
        #endif

        do {
            let (data, resp) = try await URLSession.shared.data(for: req)
            #if DEBUG
            if let body = String(data: data, encoding: .utf8) {
                print("REFRESH raw response:", body)
            }
            #endif
            guard let http = resp as? HTTPURLResponse else { throw AuthAPIError.badResponse }
            guard (200..<300).contains(http.statusCode) else { throw AuthAPIError.http(http.statusCode) }
            let lr = try JSONDecoder().decode(LoginResponse.self, from: data)
            return TokenPair(
                accessToken: lr.accessToken,
                refreshToken: lr.refreshToken,
                expiry: Date().addingTimeInterval(TimeInterval(lr.expiresIn))
            )
        } catch let e as URLError {
            throw AuthAPIError.network(e.localizedDescription)
        }
    }
}

