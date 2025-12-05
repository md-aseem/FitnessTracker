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
                            repsText: $repsText,
                            onAdd: addSet
                        )
                        if let exercise = selectedExercise {
                            Text("Current: \(exercise.name)")
                                .font(.footnote)
                                .foregroundColor(.secondary)
                        }
                    }

                    Section("Sets in this workout") {
                        if currentSets.isEmpty {
                            Text("No sets added yet.")
                                .foregroundColor(.secondary)
                        } else {
                            ForEach(currentSets) { set in
                                if let exercise = store.exercises.first(where: { $0.id == set.exerciseId }) {
                                    HStack {
                                        Text(exercise.name)
                                        Spacer()
                                        Text("\(Int(set.weight)) kg x \(set.reps)")
                                            .foregroundColor(.secondary)
                                    }
                                }
                            }
                            .onDelete(perform: deleteSet)
                        }
                    }
                }
                .scrollDismissesKeyboard(.interactively)

                Button(action: saveWorkout) {
                    Text("Save Workout")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(currentSets.isEmpty ? Color.gray.opacity(0.3) : Color.accentColor)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .padding(.horizontal)
                }
                .disabled(currentSets.isEmpty)
            }
            .navigationTitle("New Workout")
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

    private func deleteSet(at offsets: IndexSet) {
        currentSets.remove(atOffsets: offsets)
    }

    private func saveWorkout() {
        guard !currentSets.isEmpty else { return }
        store.addWorkout(sets: currentSets)
        currentSets.removeAll()
        showSavedAlert = true
    }
}

#Preview {
    WorkoutSessionView()
        .environmentObject(WorkoutStore())
}
