import Foundation

// Optional: use this to send any Encodable as the POST body generically
struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void
    init<T: Encodable>(_ wrapped: T) { _encode = wrapped.encode }
    func encode(to encoder: Encoder) throws { try _encode(encoder) }
}

enum APIClientError: LocalizedError, Equatable {
    case notHTTP
    case unauthorized        // still 401 after refresh → kick to login
    case badStatus(Int)
    case decode(String)

    var errorDescription: String? {
        switch self {
        case .notHTTP: return "Invalid server response"
        case .unauthorized: return "Session expired. Please sign in again."
        case .badStatus(let c): return "Server error (\(c))"
        case .decode(let m): return "Decode error: \(m)"
        }
    }
}

/// Central client that attaches Bearer tokens, auto-refreshes on 401 (single flight),
/// and decodes JSON. Adjust `base` to your API host.
actor AuthedClient {
    static let shared = AuthedClient()

    // Change this to your API (or expose a setter below)
    private var base = URL(string: "https://www.falowen.app")!

    // Optionally let the app set/override base at runtime (e.g., from ServerResolver)
    func setBase(_ url: URL) { base = url }

    // MARK: - Public helpers

    func getJSON<T: Decodable>(_ path: String) async throws -> T {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = "GET"
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        return try await send(req)
    }

    func postJSON<T: Decodable, B: Encodable>(_ path: String, body: B) async throws -> T {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = "POST"
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        return try await send(req)
    }

    func deleteJSON<T: Decodable>(_ path: String) async throws -> T {
        var req = URLRequest(url: base.appendingPathComponent(path))
        req.httpMethod = "DELETE"
        req.addValue("application/json", forHTTPHeaderField: "Accept")
        return try await send(req)
    }

    // MARK: - Core send with auto-refresh + single retry on 401

    private func send<T: Decodable>(_ req: URLRequest) async throws -> T {
        // 1) Attach a valid (fresh) token
        var authed = try await authorized(req)

        // 2) First attempt
        let (data1, resp1) = try await URLSession.shared.data(for: authed)
        guard let http1 = resp1 as? HTTPURLResponse else { throw APIClientError.notHTTP }

        if http1.statusCode == 401 {
            // 3) Refresh once (single-flight via TokenStore) and retry
            let pair = try await TokenStore.shared.currentPair()
            let newPair = try await TokenStore.shared.refresh(using: pair.refreshToken)
            authed = try authorizedSync(req, with: newPair.accessToken)

            let (data2, resp2) = try await URLSession.shared.data(for: authed)
            guard let http2 = resp2 as? HTTPURLResponse else { throw APIClientError.notHTTP }
            guard (200..<300).contains(http2.statusCode) else {
                if http2.statusCode == 401 { throw APIClientError.unauthorized }
                throw APIClientError.badStatus(http2.statusCode)
            }
            return try decodeJSON(T.self, from: data2)
        }

        guard (200..<300).contains(http1.statusCode) else {
            throw APIClientError.badStatus(http1.statusCode)
        }
        return try decodeJSON(T.self, from: data1)
    }

    // MARK: - Authorization helpers

    private func authorized(_ req: URLRequest) async throws -> URLRequest {
        let pair = try await TokenStore.shared.ensureFreshPair()
        return try authorizedSync(req, with: pair.accessToken)
    }

    private func authorizedSync(_ req: URLRequest, with accessToken: String) throws -> URLRequest {
        var r = req
        r.timeoutInterval = 15
        r.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        return r
    }

    // MARK: - Decode helper

    private func decodeJSON<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            if let s = String(data: data, encoding: .utf8) {
                throw APIClientError.decode(s)
            }
            throw APIClientError.decode("unknown body")
        }
    }
}

