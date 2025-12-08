import SwiftUI
import GoogleSignIn
import Combine

// MARK: - Authentication Manager
@MainActor
class AuthenticationManager: ObservableObject {
    @Published var isAuthenticated: Bool = false
    @Published var userEmail: String?
    @Published var userName: String?
    @Published var userProfileImageURL: URL?
    
    init() {
        restorePreviousSignIn()
    }
    
    func restorePreviousSignIn() {
        GIDSignIn.sharedInstance.restorePreviousSignIn { [weak self] user, error in
            if let user = user {
                self?.updateUser(user: user)
            } else {
                self?.isAuthenticated = false
            }
        }
    }
    
    func signIn() {
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let rootViewController = windowScene.windows.first?.rootViewController else {
            print("No root view controller found")
            return
        }
        
        GIDSignIn.sharedInstance.signIn(withPresenting: rootViewController) { [weak self] result, error in
            guard let self = self else { return }
            
            if let error = error {
                print("Sign in failed: \(error.localizedDescription)")
                return
            }
            
            if let user = result?.user {
                self.updateUser(user: user)
            }
        }
    }
    
    func signOut() {
        GIDSignIn.sharedInstance.signOut()
        self.isAuthenticated = false
        self.userEmail = nil
        self.userName = nil
        self.userProfileImageURL = nil
    }
    
    private func updateUser(user: GIDGoogleUser) {
        self.isAuthenticated = true
        self.userEmail = user.profile?.email
        self.userName = user.profile?.name
        self.userProfileImageURL = user.profile?.imageURL(withDimension: 100)
    }
    
    func handleURL(_ url: URL) {
        GIDSignIn.sharedInstance.handle(url)
    }
}
