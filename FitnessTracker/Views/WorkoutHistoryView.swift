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
                            HStack(spacing: 12) {
                                Image(systemName: workout.iconName(using: store.exercises))
                                    .foregroundColor(.accentColor)
                                    .font(.title2)
                                    .frame(width: 32)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(workout.title(using: store.exercises))
                                        .font(.headline)
                                    HStack(spacing: 4) {
                                        Image(systemName: "calendar")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text(workout.date, style: .date)
                                            .font(.subheadline)
                                            .foregroundColor(.secondary)
                                    }
                                }
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
    @State private var isEditing = false
    @State private var editableSets: [WorkoutSet] = []
    
    struct ExerciseSetGroup: Identifiable {
        let id = UUID()
        let exercise: Exercise
        var sets: [WorkoutSet]
    }

    func groupedSets(from sets: [WorkoutSet]) -> [ExerciseSetGroup] {
        var groups: [ExerciseSetGroup] = []
        for set in sets {
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
        _editableSets = State(initialValue: workout.sets)
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
                HStack {
                    Image(systemName: "clock")
                        .foregroundColor(.secondary)
                    Text(workout.date, style: .time)
                }
            }

            ForEach(groupedSets(from: isEditing ? editableSets : workout.sets)) { group in
                Section(header: Text(group.exercise.name)) {
                    ForEach(group.sets) { set in
                        if isEditing {
                            EditableSetRow(
                                set: set,
                                setNumber: group.sets.firstIndex(where: { $0.id == set.id })! + 1,
                                onUpdate: { updatedSet in
                                    if let index = editableSets.firstIndex(where: { $0.id == updatedSet.id }) {
                                        editableSets[index] = updatedSet
                                    }
                                }
                            )
                        } else {
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
        }
        .navigationTitle(title)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button(isEditing ? "Done" : "Edit") {
                    if isEditing {
                        // Save changes
                        store.updateWorkoutSets(workout, newSets: editableSets)
                    } else {
                        // Enter edit mode
                        editableSets = workout.sets
                    }
                    isEditing.toggle()
                }
            }
        }
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

struct EditableSetRow: View {
    let set: WorkoutSet
    let setNumber: Int
    let onUpdate: (WorkoutSet) -> Void
    
    @State private var weightText: String
    @State private var repsText: String
    
    init(set: WorkoutSet, setNumber: Int, onUpdate: @escaping (WorkoutSet) -> Void) {
        self.set = set
        self.setNumber = setNumber
        self.onUpdate = onUpdate
        _weightText = State(initialValue: "\(Int(set.weight))")
        _repsText = State(initialValue: "\(set.reps)")
    }
    
    var body: some View {
        HStack {
            Text("Set \(setNumber)")
                .foregroundColor(.secondary)
                .font(.caption)
                .frame(width: 40, alignment: .leading)
            
            Spacer()
            
            HStack(spacing: 4) {
                TextField("Weight", text: $weightText)
                    .keyboardType(.numberPad)
                    .font(.system(.body, design: .monospaced))
                    .fontWeight(.semibold)
                    .frame(width: 50)
                    .multilineTextAlignment(.trailing)
                    .textFieldStyle(.roundedBorder)
                    .onChange(of: weightText) { _, newValue in
                        updateSet()
                    }
                
                Text("lb")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text("x")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                TextField("Reps", text: $repsText)
                    .keyboardType(.numberPad)
                    .font(.system(.body, design: .monospaced))
                    .fontWeight(.semibold)
                    .frame(width: 40)
                    .multilineTextAlignment(.trailing)
                    .textFieldStyle(.roundedBorder)
                    .onChange(of: repsText) { _, newValue in
                        updateSet()
                    }
            }
        }
    }
    
    private func updateSet() {
        let weight = Double(weightText) ?? set.weight
        let reps = Int(repsText) ?? set.reps
        var updatedSet = set
        updatedSet.weight = weight
        updatedSet.reps = reps
        onUpdate(updatedSet)
    }
}

#Preview {
    NavigationStack {
        WorkoutHistoryView()
            .environmentObject(WorkoutStore())
    }
}
