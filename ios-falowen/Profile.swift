import Foundation

struct Profile: Decodable, Identifiable {
    let id: String
    let email: String
    let name: String?
}

