// content
import SwiftUI

struct ContentView: View {
    var body: some View {
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

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gearshape")
                }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(WorkoutStore())
}
