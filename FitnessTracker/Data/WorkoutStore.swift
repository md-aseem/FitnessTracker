// store
import Foundation
import SwiftUI
import SwiftUI
import Combine

@MainActor
class WorkoutStore: ObservableObject {
    @Published var exercises: [Exercise] = []
    @Published var workouts: [Workout] = []

    private let fileName = "workoutData.json"

    init() {
        load()
        if exercises.isEmpty {
            exercises = Self.defaultExercises()
        }
        
        if workouts.isEmpty {
            addDummyData()
        }
    }

    private func addDummyData() {
        // Ensure we have exercises to link to
        guard let benchPress = exercises.first(where: { $0.name == "Bench Press" }),
              let squat = exercises.first(where: { $0.name == "Squat" }),
              let deadlift = exercises.first(where: { $0.name == "Deadlift" }) else { return }
        
        var dummyWorkouts: [Workout] = []
        let calendar = Calendar.current
        let today = Date()
        
        // Generate 10 weeks of data
        for i in 0..<10 {
            guard let date = calendar.date(byAdding: .day, value: -i * 3, to: today) else { continue }
            
            // Alternating workouts
            if i % 2 == 0 {
                // Push Day (Bench Focus)
                // Weight increases as we get closer to today (smaller i)
                let baseWeight = 135.0 + Double(10 - i) * 5.0 
                let sets = [
                    WorkoutSet(exerciseId: benchPress.id, weight: baseWeight, reps: 8),
                    WorkoutSet(exerciseId: benchPress.id, weight: baseWeight + 5, reps: 6),
                    WorkoutSet(exerciseId: benchPress.id, weight: baseWeight + 10, reps: 4)
                ]
                dummyWorkouts.append(Workout(date: date, sets: sets))
            } else {
                // Leg Day
                let squatWeight = 185.0 + Double(10 - i) * 10.0
                let deadliftWeight = 225.0 + Double(10 - i) * 10.0
                let sets = [
                    WorkoutSet(exerciseId: squat.id, weight: squatWeight, reps: 5),
                    WorkoutSet(exerciseId: squat.id, weight: squatWeight, reps: 5),
                    WorkoutSet(exerciseId: deadlift.id, weight: deadliftWeight, reps: 3)
                ]
                dummyWorkouts.append(Workout(date: date, sets: sets))
            }
        }
        
        self.workouts = dummyWorkouts.sorted(by: { $0.date < $1.date })
        save()
    }

    // MARK: - Public API

    func addWorkout(sets: [WorkoutSet]) {
        let workout = Workout(date: Date(), sets: sets)
        workouts.append(workout)
        save()
    }

    func addExercise(name: String, group: ExerciseGroupType) {
        let exercise = Exercise(name: name, group: group)
        exercises.append(exercise)
        save()
    }

    func deleteExercise(_ exercise: Exercise) {
        if let index = exercises.firstIndex(where: { $0.id == exercise.id }) {
            exercises.remove(at: index)
            save()
        }
    }

    func deleteWorkout(_ workout: Workout) {
        if let index = workouts.firstIndex(where: { $0.id == workout.id }) {
            workouts.remove(at: index)
            save()
        }
    }

    func updateWorkoutDate(_ workout: Workout, newDate: Date) {
        if let index = workouts.firstIndex(where: { $0.id == workout.id }) {
            workouts[index].date = newDate
            save()
        }
    }

    func updateWorkoutSets(_ workout: Workout, newSets: [WorkoutSet]) {
        if let index = workouts.firstIndex(where: { $0.id == workout.id }) {
            workouts[index].sets = newSets
            save()
        }
    }

    func historyForExercise(_ exercise: Exercise) -> [(date: Date, set: WorkoutSet)] {
        workouts.flatMap { workout in
            workout.sets
                .filter { $0.exerciseId == exercise.id }
                .map { (date: workout.date, set: $0) }
        }
        .sorted(by: { $0.date < $1.date })
    }

    func maxWeightPerDay(for exercise: Exercise, minReps: Int = 0) -> [(date: Date, weight: Double)] {
        let groupedByDay = Dictionary(grouping: historyForExercise(exercise)) { (entry) -> Date in
            let calendar = Calendar.current
            let components = calendar.dateComponents([.year, .month, .day], from: entry.date)
            return calendar.date(from: components) ?? entry.date
        }

        return groupedByDay.compactMap { (day, entries) in
            // Filter by minimum reps
            let filteredEntries = entries.filter { $0.set.reps >= minReps }
            guard !filteredEntries.isEmpty else { return nil }
            
            let maxWeight = filteredEntries.map { $0.set.weight }.max() ?? 0
            return (date: day, weight: maxWeight)
        }
        .sorted(by: { $0.date < $1.date })
    }

    func groupName(for workout: Workout) -> String {
        let groups = workout.sets.compactMap { set in
            exercises.first(where: { $0.id == set.exerciseId })?.group
        }

        guard !groups.isEmpty else {
            return "Empty Workout"
        }

        let counts = groups.reduce(into: [:]) { counts, group in
            counts[group, default: 0] += 1
        }

        // Find the group with the maximum count
        if let (mostFrequentGroup, _) = counts.max(by: { $0.value < $1.value }) {
            // Check if it's a clear majority or if there are multiple top groups
            let maxCount = counts.values.max() ?? 0
            let topGroups = counts.filter { $0.value == maxCount }

            if topGroups.count == 1 {
                return "\(mostFrequentGroup.displayName) Day"
            } else {
                return "Mixed Day"
            }
        }

        return "Mixed Day"
    }

    // MARK: - Persistence

    private func save() {
        do {
            let data = AppData(exercises: exercises, workouts: workouts)
            let encoded = try JSONEncoder().encode(data)
            try encoded.write(to: fileURL(), options: [.atomic])
        } catch {
            print("Error saving data: \(error)")
        }
    }

    private func load() {
        do {
            let url = fileURL()
            guard FileManager.default.fileExists(atPath: url.path) else {
                return
            }
            let data = try Data(contentsOf: url)
            let decoded = try JSONDecoder().decode(AppData.self, from: data)
            self.exercises = decoded.exercises
            self.workouts = decoded.workouts
        } catch {
            print("Error loading data: \(error)")
        }
    }

    private func fileURL() -> URL {
        let manager = FileManager.default
        let docs = manager.urls(for: .documentDirectory, in: .userDomainMask).first!
        return docs.appendingPathComponent(fileName)
    }

    // MARK: - Sample Data

    static func defaultExercises() -> [Exercise] {
        [
            Exercise(name: "Bench Press", group: .push),
            Exercise(name: "Overhead Press", group: .push),
            Exercise(name: "Push-up", group: .push),

            Exercise(name: "Pull-up", group: .pull),
            Exercise(name: "Barbell Row", group: .pull),
            Exercise(name: "Lat Pulldown", group: .pull),

            Exercise(name: "Squat", group: .legs),
            Exercise(name: "Deadlift", group: .legs),
            Exercise(name: "Leg Press", group: .legs),

            Exercise(name: "Plank", group: .other),
            Exercise(name: "Bicep Curl", group: .other),
            Exercise(name: "Tricep Extension", group: .other)
        ]
    }
}
