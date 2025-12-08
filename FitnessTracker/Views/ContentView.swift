// content
import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthenticationManager
    
    var body: some View {
        if authManager.isAuthenticated {
            TabView {
                WorkoutSessionView()
                    .tabItem {
                        Label("Workout", systemImage: "figure.strengthtraining.traditional")
                    }
                
                WorkoutHistoryView()
                    .tabItem {
                        Label("History", systemImage: "clock.arrow.circlepath")
                    }
                
                ExerciseListView()
                    .tabItem {
                        Label("Exercises", systemImage: "list.bullet")
                    }
                
                BiometricsView()
                    .tabItem {
                        Label("Biometrics", systemImage: "chart.bar.doc.horizontal")
                    }
                
                SettingsView()
                    .tabItem {
                        Label("Settings", systemImage: "gearshape")
                    }
            }
        } else {
            LoginView()
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(WorkoutStore())
        .environmentObject(AuthenticationManager())
}
