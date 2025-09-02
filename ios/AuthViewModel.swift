import Foundation
#if canImport(Combine)
import Combine
#endif
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
#if canImport(WebKit)
import WebKit
#endif

#if !canImport(Combine)
protocol ObservableObject {}
@propertyWrapper struct Published<Value> {
    var wrappedValue: Value
    init(wrappedValue: Value) { self.wrappedValue = wrappedValue }
}
#endif

@MainActor
final class AuthViewModel: ObservableObject {
    /// Indicates whether the user needs to log in again.
    @Published var needsLogin = false

    #if canImport(Combine)
    private var timer: AnyCancellable?
    #endif
    private let refreshURL: URL
    private let refreshInterval: TimeInterval
    private let retryBaseDelay: TimeInterval
    private let maxRetries = 3
    nonisolated(unsafe) static var protocolClasses: [AnyClass]? = nil

    /// - Parameters:
    ///   - baseURL: Base URL of the backend server.
    ///   - maxAge: Maximum age of the session cookie in seconds.
    init(baseURL: URL, maxAge: TimeInterval = 60 * 60 * 24 * 30, retryBaseDelay: TimeInterval = 1, performInitialRefresh: Bool = true) {
        self.refreshURL = baseURL.appendingPathComponent("/auth/refresh")

        // Refresh one minute before the cookie expires.
        self.refreshInterval = maxAge - 60
        self.retryBaseDelay = retryBaseDelay

        scheduleRefresh()
        // Extend the cookie immediately when the app launches.
        if performInitialRefresh {
            refreshSession()
        }
    }

    private func scheduleRefresh() {
        #if canImport(Combine)
        timer = Timer.publish(every: refreshInterval, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.refreshSession()
            }
        #endif
    }

    func refreshSession(retryAttempt: Int = 0) {
        var config = URLSessionConfiguration.default
        // Ensure cookies from the refresh response replace the existing ones.
        config.httpCookieStorage = HTTPCookieStorage.shared
        if let classes = AuthViewModel.protocolClasses {
            config.protocolClasses = classes
        }
        let session = URLSession(configuration: config)

        var request = URLRequest(url: refreshURL)
        request.httpMethod = "GET"

        let task = session.dataTask(with: request) { [weak self] _, response, error in
            if let error {
                print("Session refresh failed: \(error)")
                guard let self = self, retryAttempt < self.maxRetries else { return }
                let delay = self.retryBaseDelay * pow(2, Double(retryAttempt))
                DispatchQueue.main.asyncAfter(deadline: .now() + delay) {
                    self.refreshSession(retryAttempt: retryAttempt + 1)
                }
                return
            }

            guard let httpResponse = response as? HTTPURLResponse else { return }
            if httpResponse.statusCode == 401 {
                DispatchQueue.main.async {
                    // Prompt the user to log in again on 401 responses.
                    self?.needsLogin = true
                }
            }
        }
        task.resume()
    }

#if canImport(WebKit)
    /// Copies cookies from a WebKit `WKHTTPCookieStore` into `HTTPCookieStorage.shared` so
    /// subsequent `URLSession` requests reuse them.
    func syncCookies(from cookieStore: WKHTTPCookieStore) {
        cookieStore.getAllCookies { cookies in
            for cookie in cookies {
                HTTPCookieStorage.shared.setCookie(cookie)
            }
        }
    }
#endif

    /// Retrieve the current session token from ``HTTPCookieStorage.shared``.
    /// - Returns: The session token if present.
    func loadToken() -> String? {
        HTTPCookieStorage.shared.cookies?
            .first(where: { $0.name == "session" })?
            .value
    }
}
