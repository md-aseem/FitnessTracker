// history
import SwiftUI

struct WorkoutHistoryView: View {
    @EnvironmentObject var store: WorkoutStore

    @State private var workoutToDelete: Workout?
    @State private var showDeleteConfirmation = false

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
                                Text(workout.title(using: store.exercises))
                                    .font(.headline)
                                Text(workout.date, style: .date)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                    .onDelete(perform: deleteWorkout)
                }
            }
            .navigationTitle("Workout History")
            .alert("Delete Workout", isPresented: $showDeleteConfirmation, presenting: workoutToDelete) { workout in
                Button("Delete", role: .destructive) {
                    store.deleteWorkout(workout)
                }
                Button("Cancel", role: .cancel) {}
            } message: { workout in
                Text("Are you sure you want to delete this workout? This action cannot be undone.")
            }
        }
    }

    private func deleteWorkout(at offsets: IndexSet) {
        if let index = offsets.first {
            workoutToDelete = sortedWorkouts[index]
            showDeleteConfirmation = true
        }
    }


}

struct WorkoutDetailView: View {
    @EnvironmentObject var store: WorkoutStore
    let workout: Workout
    
    @State private var showDatePicker = false
    @State private var selectedDate: Date
    
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

    init(workout: Workout) {
        self.workout = workout
        _selectedDate = State(initialValue: workout.date)
    }

    var title: String {
        workout.title(using: store.exercises)
    }

    var body: some View {
        List {
            Section {
                Button(action: {
                    showDatePicker = true
                }) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Date")
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Text(workout.date, style: .date)
                                .foregroundColor(.primary)
                        }
                        Spacer()
                        Image(systemName: "calendar")
                            .foregroundColor(.blue)
                    }
                }
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
        .navigationTitle(title)
        .sheet(isPresented: $showDatePicker) {
            NavigationStack {
                VStack {
                    DatePicker(
                        "Select Date",
                        selection: $selectedDate,
                        displayedComponents: [.date, .hourAndMinute]
                    )
                    .datePickerStyle(.graphical)
                    .padding()
                    
                    Spacer()
                }
                .navigationTitle("Edit Date")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") {
                            selectedDate = workout.date
                            showDatePicker = false
                        }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Done") {
                            store.updateWorkoutDate(workout, newDate: selectedDate)
                            showDatePicker = false
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        WorkoutHistoryView()
            .environmentObject(WorkoutStore())
    }
}
