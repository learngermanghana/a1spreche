import Foundation
import Combine

@MainActor
final class AuthViewModel: ObservableObject {
    /// Indicates whether the user needs to log in again.
    @Published var needsLogin = false

    private var timer: AnyCancellable?
    private let refreshURL: URL
    private let refreshInterval: TimeInterval

    /// - Parameters:
    ///   - baseURL: Base URL of the backend server.
    ///   - maxAge: Maximum age of the session cookie in seconds.
    init(baseURL: URL, maxAge: TimeInterval = 60 * 60 * 24 * 30) {
        self.refreshURL = baseURL.appendingPathComponent("/auth/refresh")
        // Safari's Intelligent Tracking Prevention purges cookies that aren't
        // updated within roughly a week. Refresh at least daily (or half the
        // cookie's declared lifetime) so the session stays alive well before
        // the retention window closes.
        self.refreshInterval = min(maxAge / 2, 60 * 60 * 24)
        scheduleRefresh()
        // Extend the cookie immediately when the app launches.
        refreshSession()
    }

    private func scheduleRefresh() {
        timer = Timer.publish(every: refreshInterval, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.refreshSession()
            }
    }

    private func refreshSession() {
        var config = URLSessionConfiguration.default
        // Ensure cookies from the refresh response replace the existing ones.
        config.httpCookieStorage = HTTPCookieStorage.shared
        let session = URLSession(configuration: config)

        var request = URLRequest(url: refreshURL)
        request.httpMethod = "GET"

        let task = session.dataTask(with: request) { [weak self] _, response, _ in
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
}
