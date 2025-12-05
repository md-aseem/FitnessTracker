// exercises
import SwiftUI

struct ExerciseListView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showAddExercise = false
    @State private var newExerciseName = ""
    @State private var newExerciseGroup: ExerciseGroupType = .push
    @State private var exerciseToDelete: Exercise?
    @State private var showDeleteConfirmation = false

    var body: some View {
        NavigationStack {
            List {
                ForEach(ExerciseGroupType.allCases) { group in
                    Section(group.displayName) {
                        let items = store.exercises.filter { $0.group == group }
                        if items.isEmpty {
                            Text("No exercises in this group.")
                                .foregroundColor(.secondary)
                        } else {
                            ForEach(items) { exercise in
                                NavigationLink {
                                    ExerciseHistoryView(exercise: exercise)
                                } label: {
                                    Text(exercise.name)
                                }
                            }
                            .onDelete { offsets in
                                deleteExercise(at: offsets, in: group)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Exercises")
            .toolbar {
                Button {
                    showAddExercise = true
                } label: {
                    Image(systemName: "plus")
                }
            }
            .sheet(isPresented: $showAddExercise) {
                NavigationStack {
                    Form {
                        TextField("Exercise name", text: $newExerciseName)

                        Picker("Group", selection: $newExerciseGroup) {
                            ForEach(ExerciseGroupType.allCases) { group in
                                Text(group.displayName).tag(group)
                            }
                        }
                    }
                    .navigationTitle("New Exercise")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Cancel") {
                                showAddExercise = false
                            }
                        }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Add") {
                                addExercise()
                            }
                            .disabled(newExerciseName.trimmingCharacters(in: .whitespaces).isEmpty)
                        }
                    }
                }
            }
            .alert("Delete Exercise", isPresented: $showDeleteConfirmation, presenting: exerciseToDelete) { exercise in
                Button("Delete", role: .destructive) {
                    store.deleteExercise(exercise)
                }
                Button("Cancel", role: .cancel) {}
            } message: { exercise in
                Text("Are you sure you want to delete '\(exercise.name)'? This action cannot be undone.")
            }
        }
    }

    private func addExercise() {
        let trimmed = newExerciseName.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        store.addExercise(name: trimmed, group: newExerciseGroup)
        newExerciseName = ""
        newExerciseGroup = .push
        showAddExercise = false
    }

    private func deleteExercise(at offsets: IndexSet, in group: ExerciseGroupType) {
        let items = store.exercises.filter { $0.group == group }
        if let index = offsets.first {
            exerciseToDelete = items[index]
            showDeleteConfirmation = true
        }
    }
}

#Preview {
    ExerciseListView()
        .environmentObject(WorkoutStore())
}
