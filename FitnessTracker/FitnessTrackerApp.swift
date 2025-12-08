import SwiftUI

@main
struct FitnessTrackerApp: App {
    @StateObject private var workoutStore = WorkoutStore()
    @StateObject private var authManager = AuthenticationManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(workoutStore)
                .environmentObject(authManager)
                .onOpenURL { url in
                    authManager.handleURL(url)
                }
        }
    }
}
