import SwiftUI
import UIKit

struct RootView: View {
    @EnvironmentObject var auth: AuthViewModel

    var body: some View {
        Group {
            if auth.isAuthenticated {
                ContentView()
            } else {
                LoginView()
            }
        }
        // Run once when the app starts
        .onAppear {
            Task { await auth.bootstrap() }
        }
        // Run again whenever the app returns to foreground
        .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
            Task { await auth.bootstrap() }
        }
        // Smooth transition between login/content
        .animation(.easeInOut, value: auth.isAuthenticated)
    }
}

