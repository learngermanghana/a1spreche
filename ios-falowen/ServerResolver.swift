
import Foundation

// Resolves the API base URL automatically.
// Order:
// 1) UserDefaults override (persisted after first success)
// 2) Info.plist key: API_BASE_URL
// 3) DEBUG (Simulator): try local dev candidates (http://127.0.0.1:3000, http://localhost:3000)
// 4) Bonjour-style mDNS: http://falowen.local:3000 (if your dev machine advertises this)
// 5) Fallback to a production placeholder: https://www.falowen.com (change this when you have one)
//
// It pings candidates with GET /health (or /) and picks the first that returns HTTP 200.
// The chosen URL is stored in UserDefaults for next launch.

actor ServerResolver {
    static let shared = ServerResolver()

    private let defaultsKey = "falowen.api.baseurl"
    private(set) var baseURL: URL = URL(string: "https://www.falowen.com")! // fallback; change if you have a prod domain

    // Call once on app launch
    func discover() async {
        // 1) UserDefaults
        if let saved = UserDefaults.standard.string(forKey: defaultsKey), let url = URL(string: saved) {
            baseURL = url
            return
        }
        // 2) Info.plist
        if let plist = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String,
           let url = URL(string: plist) {
            baseURL = url
            UserDefaults.standard.set(url.absoluteString, forKey: defaultsKey)
            return
        }

        // 3/4) Probe candidates
        let candidates: [String] = {
            #if DEBUG
            #if targetEnvironment(simulator)
            return [
                "http://127.0.0.1:3000",
                "http://localhost:3000",
                "http://falowen.local:3000",
                "https://api.falowen.com"
            ]
            #else
            return [
                "http://falowen.local:3000", // your dev Mac via mDNS (optional)
                "https://api.falowen.com"
            ]
            #endif
            #else
            return ["https://api.falowen.com"]
            #endif
        }()

        for s in candidates {
            if let url = URL(string: s), await isHealthy(base: url) {
                baseURL = url
                UserDefaults.standard.set(url.absoluteString, forKey: defaultsKey)
                return
            }
        }
    }

    private func isHealthy(base: URL) async -> Bool {
        // Try /health then /
        let paths = ["/health", "/"]
        for p in paths {
            var req = URLRequest(url: base.appendingPathComponent(p))
            req.httpMethod = "GET"
            req.timeoutInterval = 1.5
            do {
                let (_, resp) = try await URLSession.shared.data(for: req)
                if let http = resp as? HTTPURLResponse, (200..<300).contains(http.statusCode) {
                    return true
                }
            } catch {
                continue
            }
        }
        return false
    }
}

