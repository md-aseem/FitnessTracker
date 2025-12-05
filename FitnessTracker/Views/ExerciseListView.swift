// exercises
import SwiftUI

struct ExerciseListView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showAddExercise = false
    @State private var newExerciseName = ""
    @State private var newExerciseGroup: ExerciseGroupType = .push

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
        offsets.forEach { index in
            let exercise = items[index]
            store.deleteExercise(exercise)
        }
    }
}

#Preview {
    ExerciseListView()
        .environmentObject(WorkoutStore())
}
