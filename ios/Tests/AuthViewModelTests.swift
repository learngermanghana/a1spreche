import XCTest
import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
#if canImport(WebKit)
import WebKit
#endif
@testable import AuthViewModelModule

class URLProtocolMock: URLProtocol {
    nonisolated(unsafe) static var responses: [() -> (HTTPURLResponse?, Data?, Error?)] = []
    nonisolated(unsafe) static var requestCount = 0

    override class func canInit(with request: URLRequest) -> Bool {
        true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        request
    }

    override func startLoading() {
        let index = URLProtocolMock.requestCount
        URLProtocolMock.requestCount += 1
        let (response, data, error) = URLProtocolMock.responses[index]()
        if let response = response {
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        }
        if let data = data {
            client?.urlProtocol(self, didLoad: data)
        }
        if let error = error {
            client?.urlProtocol(self, didFailWithError: error)
        } else {
            client?.urlProtocolDidFinishLoading(self)
        }
    }

    override func stopLoading() {}
}

@MainActor
final class AuthViewModelTests: XCTestCase {
    override func setUp() {
        super.setUp()
        URLProtocolMock.requestCount = 0
        URLProtocolMock.responses = []
        AuthViewModel.protocolClasses = [URLProtocolMock.self]
        if let cookies = HTTPCookieStorage.shared.cookies {
            for cookie in cookies {
                HTTPCookieStorage.shared.deleteCookie(cookie)
            }
        }
    }

    override func tearDown() {
        AuthViewModel.protocolClasses = nil
        super.tearDown()
    }

    func testNeedsLoginTogglesOn401() async throws {
        let url = URL(string: "https://example.com")!
        URLProtocolMock.responses = [{
            let response = HTTPURLResponse(url: url, statusCode: 401, httpVersion: nil, headerFields: nil)!
            return (response, nil, nil)
        }]

        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1, performInitialRefresh: false)
        vm.refreshSession()

        try await Task.sleep(nanoseconds: UInt64(0.3 * 1_000_000_000))
        XCTAssertTrue(vm.needsLogin)
    }

    func testRefreshRetriesOnNetworkError() async throws {
        let url = URL(string: "https://example.com")!
        URLProtocolMock.responses = [
            {
                let error = NSError(domain: NSURLErrorDomain, code: NSURLErrorTimedOut)
                return (nil, nil, error)
            },
            {
                let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: nil, headerFields: nil)!
                return (response, nil, nil)
            }
        ]

        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1, performInitialRefresh: false)
        vm.refreshSession()

        try await Task.sleep(nanoseconds: UInt64(0.5 * 1_000_000_000))
        XCTAssertEqual(URLProtocolMock.requestCount, 2)
        XCTAssertFalse(vm.needsLogin)
    }

#if canImport(WebKit)
    func testSyncCookiesCopiesToSharedStorage() async throws {
        let cookie = HTTPCookie(properties: [
            .domain: "example.com",
            .path: "/",
            .name: "session",
            .value: "abc",
        ])!

        class CookieStoreMock: WKHTTPCookieStore {
            let cookies: [HTTPCookie]
            init(cookies: [HTTPCookie]) { self.cookies = cookies }
            override func getAllCookies(_ completionHandler: @escaping ([HTTPCookie]) -> Void) {
                completionHandler(cookies)
            }
        }

        let store = CookieStoreMock(cookies: [cookie])

        let url = URL(string: "https://example.com")!
        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1, performInitialRefresh: false)
        vm.syncCookies(from: store)

        try await Task.sleep(nanoseconds: UInt64(0.2 * 1_000_000_000))
        let stored = HTTPCookieStorage.shared.cookies?.first(where: { $0.name == "session" })
        XCTAssertEqual(stored?.value, "abc")
    }
#endif

    func testLoadTokenAllowsRefreshWithoutLogin() async throws {
        let cookie = HTTPCookie(properties: [
            .domain: "example.com",
            .path: "/",
            .name: "session",
            .value: "token123",
        ])!
        HTTPCookieStorage.shared.setCookie(cookie)

        let url = URL(string: "https://example.com")!
        URLProtocolMock.responses = [{
            let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, nil, nil)
        }]

        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1, performInitialRefresh: false)
        XCTAssertEqual(vm.loadToken(), "token123")
        vm.refreshSession()

        try await Task.sleep(nanoseconds: UInt64(0.2 * 1_000_000_000))
        XCTAssertFalse(vm.needsLogin)
    }
}
