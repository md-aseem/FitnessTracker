// exercise history
import SwiftUI
import Charts

struct ExerciseHistoryView: View {
    @EnvironmentObject var store: WorkoutStore
    let exercise: Exercise
    
    @State private var minReps: Int = 6

    struct DataPoint: Identifiable {
        let id = UUID()
        let date: Date
        let weight: Double
    }

    var dataPoints: [DataPoint] {
        store.maxWeightPerDay(for: exercise, minReps: minReps).map { (date, weight) in
            DataPoint(date: date, weight: weight)
        }
    }
    
    var minWeight: Double {
        let weights = dataPoints.map { $0.weight }
        guard let min = weights.min() else { return 0 }
        // Add 10% padding below minimum
        return max(0, min - (min * 0.1))
    }
    
    var maxWeight: Double {
        let weights = dataPoints.map { $0.weight }
        guard let max = weights.max() else { return 100 }
        // Add 10% padding above maximum
        return max + (max * 0.1)
    }

    struct SetWrapper: Identifiable {
        let id = UUID()
        let set: WorkoutSet
        let index: Int
        let isMaxWeight: Bool
    }

    struct GroupedSets: Identifiable {
        let id = UUID()
        let date: Date
        let sets: [SetWrapper]
    }

    var groupedHistory: [GroupedSets] {
        let entries = store.historyForExercise(exercise)
        let grouped = Dictionary(grouping: entries) { entry -> Date in
            Calendar.current.startOfDay(for: entry.date)
        }
        
        return grouped.map { (date, entries) in
            let sortedEntries = entries.sorted { $0.date < $1.date } // Sort by time within the day
            
            // Find max weight among sets meeting the minimum reps criteria
            let validSets = sortedEntries.filter { $0.set.reps >= minReps }
            let maxWeight = validSets.map { $0.set.weight }.max() ?? 0
            
            let setWrappers = sortedEntries.enumerated().map { index, entry in
                SetWrapper(
                    set: entry.set,
                    index: index + 1,
                    isMaxWeight: entry.set.reps >= minReps && entry.set.weight == maxWeight
                )
            }
            
            return GroupedSets(date: date, sets: setWrappers)
        }
        .sorted { $0.date > $1.date }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                
                HStack(spacing: 6) {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                        .foregroundColor(.accentColor)
                    Text("Max Weight Over Time")
                        .font(.headline)
                }
                .padding(.horizontal)
                
                HStack {
                    Image(systemName: "line.3.horizontal.decrease.circle.fill")
                        .foregroundColor(.orange)
                    Text("Min. Reps:")
                        .font(.subheadline)
                    Stepper(value: $minReps, in: 1...20) {
                        Text("\(minReps)")
                            .font(.system(.body, design: .monospaced))
                            .fontWeight(.semibold)
                    }
                }
                .padding(.horizontal)

                if dataPoints.isEmpty {
                    Text("No data yet for this exercise.")
                        .foregroundColor(.secondary)
                        .padding()
                } else {
                    Chart(dataPoints) { point in
                        LineMark(
                            x: .value("Date", point.date),
                            y: .value("Weight", point.weight)
                        )
                        PointMark(
                            x: .value("Date", point.date),
                            y: .value("Weight", point.weight)
                        )
                    }
                    .frame(height: 240)
                    .padding(.horizontal)
                    .chartYScale(domain: minWeight...maxWeight)
                    .chartYAxis {
                        AxisMarks(position: .leading) { value in
                            AxisGridLine()
                            AxisTick()
                            AxisValueLabel {
                                if let weight = value.as(Double.self) {
                                    Text("\(Int(weight)) lb")
                                        .font(.caption)
                                }
                            }
                        }
                    }
                    .chartXAxis {
                        AxisMarks(values: .automatic) { _ in
                            AxisGridLine()
                            AxisTick()
                            AxisValueLabel(format: .dateTime.month().day())
                        }
                    }
                }

                Divider()
                    .padding(.horizontal)

                HStack(spacing: 6) {
                    Image(systemName: "list.bullet.rectangle")
                        .foregroundColor(.accentColor)
                    Text("All Sets")
                        .font(.headline)
                }
                .padding(.horizontal)

                if groupedHistory.isEmpty {
                    Text("No sets logged yet.")
                        .foregroundColor(.secondary)
                        .padding(.horizontal)
                } else {
                    ForEach(groupedHistory) { group in
                        Section(header: Text(group.date, style: .date).font(.subheadline).bold().foregroundColor(.secondary)) {
                            ForEach(group.sets) { setWrapper in
                                HStack {
                                    Text("Set \(setWrapper.index)")
                                        .foregroundColor(.secondary)
                                        .font(.caption)
                                        .frame(width: 40, alignment: .leading)

                                    Spacer()

                                    HStack(spacing: 4) {
                                        Text("\(Int(setWrapper.set.weight))")
                                            .font(.system(.body, design: .monospaced))
                                            .fontWeight(setWrapper.isMaxWeight ? .black : .semibold)
                                            .foregroundColor(setWrapper.isMaxWeight ? .accentColor : .primary)
                                        Text("lb")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text("x")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text("\(setWrapper.set.reps)")
                                            .font(.system(.body, design: .monospaced))
                                            .fontWeight(.semibold)
                                    }
                                    

                                }
                                .padding(.horizontal)
                                .padding(.vertical, 4)
                                .background(setWrapper.isMaxWeight ? Color.accentColor.opacity(0.1) : Color.clear)
                                .cornerRadius(8)
                            }
                        }
                        .padding(.horizontal)
                    }
                }
            }
            .padding(.top)
        }
        .navigationTitle(exercise.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        ExerciseHistoryView(exercise: Exercise(name: "Bench Press", group: .push))
            .environmentObject(WorkoutStore())
    }
}
