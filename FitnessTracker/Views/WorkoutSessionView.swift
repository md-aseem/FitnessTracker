// session
import SwiftUI

struct WorkoutSessionView: View {
    @EnvironmentObject var store: WorkoutStore

    @State private var selectedGroup: ExerciseGroupType = .push
    @State private var selectedExercise: Exercise?
    @State private var weightText: String = ""
    @State private var repsText: String = ""
    @State private var currentSets: [WorkoutSet] = []
    @State private var showSavedAlert = false

    var filteredExercises: [Exercise] {
        store.exercises.filter { $0.group == selectedGroup }
    }

    struct ExerciseSetGroup: Identifiable {
        let id = UUID()
        let exercise: Exercise
        var sets: [WorkoutSet]
    }

    var groupedSets: [ExerciseSetGroup] {
        var groups: [ExerciseSetGroup] = []
        for set in currentSets {
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
        NavigationStack {
            VStack {
                Form {
                    Section("Exercise") {
                        Picker("Group", selection: $selectedGroup) {
                            ForEach(ExerciseGroupType.allCases) { group in
                                Text(group.displayName).tag(group)
                            }
                        }

                        Picker("Exercise", selection: $selectedExercise) {
                            Text("Select exercise").tag(Optional<Exercise>.none)
                            ForEach(filteredExercises) { exercise in
                                Text(exercise.name).tag(Optional(exercise))
                            }
                        }
                    }

                    Section("Add Set") {
                        SetInputRow(
                            weightText: $weightText,
                            repsText: $repsText
                        )
                        Button(action: addSet) {
                            Text("Add Set")
                                .font(.headline)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 12)
                                .background(canAddSet ? Color.accentColor : Color.gray.opacity(0.3))
                                .foregroundColor(.white)
                                .cornerRadius(10)
                        }
                        .disabled(!canAddSet)
                        .buttonStyle(.plain)
                        if let exercise = selectedExercise {
                            Text("Current: \(exercise.name)")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                        }
                    }

                    if currentSets.isEmpty {
                        Section {
                            Text("No sets added yet.")
                                .foregroundColor(.secondary)
                                .italic()
                        }
                    } else {
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
                                            Text("kg")
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
                                .onDelete { offsets in
                                    deleteSet(in: group, at: offsets)
                                }
                            }
                        }
                        
                        Section(footer: volumeFooter) {
                            EmptyView()
                        }
                    }
                }
                .scrollDismissesKeyboard(.interactively)

                // Save button moved to toolbar
            }
            .navigationTitle("New Workout")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        saveWorkout()
                    }
                    .disabled(currentSets.isEmpty)
                }
            }
            .alert("Workout saved!", isPresented: $showSavedAlert) {
                Button("OK", role: .cancel) { }
            }
        }
    }

    private func addSet() {
        guard let exercise = selectedExercise else { return }
        guard let weight = Double(weightText), weight > 0 else { return }
        guard let reps = Int(repsText), reps > 0 else { return }

        let newSet = WorkoutSet(exerciseId: exercise.id, weight: weight, reps: reps)
        currentSets.append(newSet)

        weightText = ""
        repsText = ""
    }

    private func deleteSet(in group: ExerciseSetGroup, at offsets: IndexSet) {
        let setsToDelete = offsets.map { group.sets[$0] }
        currentSets.removeAll { set in
            setsToDelete.contains(where: { $0.id == set.id })
        }
    }

    private func saveWorkout() {
        guard !currentSets.isEmpty else { return }
        store.addWorkout(sets: currentSets)
        currentSets.removeAll()
        showSavedAlert = true
    }


    private var volumeFooter: some View {
        Group {
            if !currentSets.isEmpty {
                let totalVolume = currentSets.reduce(0) { $0 + ($1.weight * Double($1.reps)) }
                Text("Total Volume: \(Int(totalVolume)) kg")
            }
        }

    }

    private var canAddSet: Bool {
        guard let weight = Double(weightText), weight > 0 else { return false }
        guard let reps = Int(repsText), reps > 0 else { return false }
        return selectedExercise != nil
    }
}

#Preview {
    WorkoutSessionView()
        .environmentObject(WorkoutStore())
}
