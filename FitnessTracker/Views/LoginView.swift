import SwiftUI
import GoogleSignInSwift

struct LoginView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    
    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            
            Image(systemName: "figure.run.circle.fill")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 120, height: 120)
                .foregroundStyle(.blue)
            
            Text("Fitness Tracker")
                .font(.largeTitle)
                .fontWeight(.bold)
            
            Text("Track your workouts and progress")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            GoogleSignInButton(action: {
                authManager.signIn()
            })
            .frame(height: 50)
            .padding(.horizontal)
            
            Spacer()
        }
        .padding()
    }
}

#Preview {
    LoginView()
        .environmentObject(AuthenticationManager())
}
