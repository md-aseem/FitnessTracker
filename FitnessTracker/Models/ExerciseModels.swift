// models
import Foundation

enum ExerciseGroupType: String, CaseIterable, Codable, Identifiable {
    case push
    case pull
    case legs
    case other

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .push: return "Push"
        case .pull: return "Pull"
        case .legs: return "Legs"
        case .other: return "Other"
        }
    }
}

struct Exercise: Identifiable, Codable, Hashable {
    let id: UUID
    var name: String
    var group: ExerciseGroupType

    init(id: UUID = UUID(), name: String, group: ExerciseGroupType) {
        self.id = id
        self.name = name
        self.group = group
    }
}

struct WorkoutSet: Identifiable, Codable {
    let id: UUID
    var exerciseId: UUID
    var weight: Double
    var reps: Int

    init(id: UUID = UUID(), exerciseId: UUID, weight: Double, reps: Int) {
        self.id = id
        self.exerciseId = exerciseId
        self.weight = weight
        self.reps = reps
    }
}

struct Workout: Identifiable, Codable {
    let id: UUID
    var date: Date
    var sets: [WorkoutSet]

    init(id: UUID = UUID(), date: Date = Date(), sets: [WorkoutSet]) {
        self.id = id
        self.date = date
        self.sets = sets
    }
}

/// Wrapper for saving/loading everything in one file
struct AppData: Codable {
    var exercises: [Exercise]
    var workouts: [Workout]
}
