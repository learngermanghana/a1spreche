import XCTest
import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
@testable import AuthViewModelModule

@MainActor
class URLProtocolMock: URLProtocol {
    static var responses: [() -> (HTTPURLResponse?, Data?, Error?)] = []
    static var requestCount = 0

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
        URLProtocol.registerClass(URLProtocolMock.self)
        URLProtocolMock.requestCount = 0
        URLProtocolMock.responses = []
        if let cookies = HTTPCookieStorage.shared.cookies {
            for cookie in cookies {
                HTTPCookieStorage.shared.deleteCookie(cookie)
            }
        }
    }

    override func tearDown() {
        URLProtocol.unregisterClass(URLProtocolMock.self)
        super.tearDown()
    }

    func testNeedsLoginTogglesOn401() async throws {
        let url = URL(string: "https://example.com")!
        URLProtocolMock.responses = [{
            let response = HTTPURLResponse(url: url, statusCode: 401, httpVersion: nil, headerFields: nil)!
            return (response, nil, nil)
        }]

        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1)
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

        let vm = AuthViewModel(baseURL: url, retryBaseDelay: 0.1)
        vm.refreshSession()

        try await Task.sleep(nanoseconds: UInt64(0.5 * 1_000_000_000))
        XCTAssertEqual(URLProtocolMock.requestCount, 2)
        XCTAssertFalse(vm.needsLogin)
    }
}
