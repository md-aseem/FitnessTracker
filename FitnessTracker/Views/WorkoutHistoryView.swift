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
    
    struct ExerciseSetGroup: Identifiable {
        let id = UUID()
        let exercise: Exercise
        var sets: [WorkoutSet]
    }

    var groupedSets: [ExerciseSetGroup] {
        var groups: [ExerciseSetGroup] = []
        for set in workout.sets {
            if let lastGroup = groups.last, lastGroup.exercise.id == set.exerciseId {
                groups[groups.count - 1].sets.append(set)
            } else {
                if let exercise = store.exercises.first(where: { $0.id == set.exerciseId }) {
                    groups.append(ExerciseSetGroup(exercise: exercise, sets: [set]))
                }
            }
        }
        return groups
    }

    var body: some View {
        List {
            Section {
                Text(workout.date, style: .date)
                Text(workout.date, style: .time)
            }

            ForEach(groupedSets) { group in
                Section(header: Text(group.exercise.name)) {
                    ForEach(group.sets) { set in
                        HStack {
                            Text("Set \(group.sets.firstIndex(where: { $0.id == set.id })! + 1)")
                                .foregroundColor(.secondary)
                                .font(.caption)
                                .frame(width: 40, alignment: .leading)
                            
                            Spacer()
                            
                            HStack(spacing: 4) {
                                Text("\(Int(set.weight))")
                                    .font(.system(.body, design: .monospaced))
                                    .fontWeight(.semibold)
                                Text("lb")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text("x")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text("\(set.reps)")
                                    .font(.system(.body, design: .monospaced))
                                    .fontWeight(.semibold)
                            }
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
