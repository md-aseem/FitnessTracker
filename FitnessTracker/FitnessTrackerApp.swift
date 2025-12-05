import SwiftUI

@main
struct FitnessTrackerApp: App {
    @StateObject private var workoutStore = WorkoutStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(workoutStore)
        }
    }
}
