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
    
    var iconName: String {
        switch self {
        case .push: return "figure.arms.open"
        case .pull: return "figure.mixed.cardio"
        case .legs: return "figure.walk"
        case .other: return "dumbbell"
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
    
    func title(using exercises: [Exercise]) -> String {
        let exerciseIds = sets.map { $0.exerciseId }
        var groupCounts: [ExerciseGroupType: Int] = [:]
        
        for id in exerciseIds {
            if let exercise = exercises.first(where: { $0.id == id }) {
                groupCounts[exercise.group, default: 0] += 1
            }
        }
        
        if let maxGroup = groupCounts.max(by: { $0.value < $1.value })?.key {
            return "\(maxGroup.displayName) Day"
        }
        
        return "Workout"
    }
    
    func iconName(using exercises: [Exercise]) -> String {
        let exerciseIds = sets.map { $0.exerciseId }
        var groupCounts: [ExerciseGroupType: Int] = [:]
        
        for id in exerciseIds {
            if let exercise = exercises.first(where: { $0.id == id }) {
                groupCounts[exercise.group, default: 0] += 1
            }
        }
        
        if let maxGroup = groupCounts.max(by: { $0.value < $1.value })?.key {
            return maxGroup.iconName
        }
        
        return "dumbbell"
    }
}

/// Wrapper for saving/loading everything in one file
struct AppData: Codable {
    var exercises: [Exercise]
    var workouts: [Workout]
}
