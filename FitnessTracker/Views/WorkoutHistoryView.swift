// history
import SwiftUI

struct WorkoutHistoryView: View {
    @EnvironmentObject var store: WorkoutStore

    var sortedWorkouts: [Workout] {
        store.workouts.sorted(by: { $0.date > $1.date })
    }

    var body: some View {
        NavigationStack {
            List {
                if sortedWorkouts.isEmpty {
                    Text("No workouts yet.")
                        .foregroundColor(.secondary)
                } else {
                    ForEach(sortedWorkouts) { workout in
                        NavigationLink {
                            WorkoutDetailView(workout: workout)
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(workoutTitle(for: workout))
                                    .font(.headline)
                                Text(workout.date, style: .date)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Workout History")
        }
    }

    func workoutTitle(for workout: Workout) -> String {
        // Gather all exercise IDs from the sets
        let exerciseIds = workout.sets.map { $0.exerciseId }
        
        // Count occurrences of each group
        var groupCounts: [ExerciseGroupType: Int] = [:]
        
        for id in exerciseIds {
            if let exercise = store.exercises.first(where: { $0.id == id }) {
                groupCounts[exercise.group, default: 0] += 1
            }
        }
        
        // Find the group with the highest count
        if let maxGroup = groupCounts.max(by: { $0.value < $1.value })?.key {
            return "\(maxGroup.displayName) Day"
        }
        
        return "Workout"
    }
}

struct WorkoutDetailView: View {
    @EnvironmentObject var store: WorkoutStore
    let workout: Workout

    var body: some View {
        List {
            Section {
                Text(workout.date, style: .date)
                Text(workout.date, style: .time)
            }

            Section("Sets") {
                ForEach(workout.sets) { set in
                    if let exercise = store.exercises.first(where: { $0.id == set.exerciseId }) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(exercise.name)
                                    .font(.headline)
                                Text("\(set.reps) reps")
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Text("\(Int(set.weight)) lb")
                                .bold()
                        }
                    }
                }
            }
        }
        .navigationTitle("Workout Detail")
    }
}

#Preview {
    NavigationStack {
        WorkoutHistoryView()
            .environmentObject(WorkoutStore())
    }
}
