#if canImport(SwiftUI) && canImport(WebKit)
import SwiftUI
import WebKit

/// A `WKWebView` wrapper used for user authentication flows.
/// When navigation reaches `completionURL` we sync cookies from the web view
/// into `HTTPCookieStorage.shared` so subsequent `URLSession` requests can reuse
/// them.
struct LoginWebView: UIViewRepresentable {
    @ObservedObject var viewModel: AuthViewModel
    let loginURL: URL
    /// URL indicating that authentication has completed successfully.
    let completionURL: URL

    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView()
        webView.navigationDelegate = context.coordinator
        webView.load(URLRequest(url: loginURL))
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        let parent: LoginWebView

        init(_ parent: LoginWebView) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let url = navigationAction.request.url,
               url == parent.completionURL {
                parent.viewModel.syncCookies(from: webView.configuration.websiteDataStore.httpCookieStore)
            }
            decisionHandler(.allow)
        }
    }
}
#endif
