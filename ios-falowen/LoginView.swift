import SwiftUI

struct LoginView: View {
    @EnvironmentObject var auth: AuthViewModel
    @State private var email = ""
    @State private var password = ""

    var body: some View {
        VStack(spacing: 16) {
            Text("Falowen Sign In").font(.title.bold())

            VStack(spacing: 12) {
                TextField("Email", text: $email)
                    .textContentType(.username)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .textFieldStyle(.roundedBorder)

                SecureField("Password", text: $password)
                    .textContentType(.password)
                    .textFieldStyle(.roundedBorder)
            }
            .padding(.horizontal)

            Button("Sign In") {
                Task { await auth.login(email: email, password: password) }
            }
            .buttonStyle(.borderedProminent)
            .disabled(email.isEmpty || password.isEmpty)

            if let err = auth.errorMessage {
                Text(err).foregroundColor(.red).font(.footnote)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding()
    }
}

