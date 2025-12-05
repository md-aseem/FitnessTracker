// exercise history
import SwiftUI
import Charts

struct ExerciseHistoryView: View {
    @EnvironmentObject var store: WorkoutStore
    let exercise: Exercise

    struct DataPoint: Identifiable {
        let id = UUID()
        let date: Date
        let weight: Double
    }

    var dataPoints: [DataPoint] {
        store.maxWeightPerDay(for: exercise).map { (date, weight) in
            DataPoint(date: date, weight: weight)
        }
    }

    var historyEntries: [(date: Date, set: WorkoutSet)] {
        store.historyForExercise(exercise).sorted(by: { $0.date > $1.date })
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {

                if dataPoints.isEmpty {
                    Text("No data yet for this exercise.")
                        .foregroundColor(.secondary)
                        .padding()
                } else {
                    Text("Max Weight Over Time")
                        .font(.headline)
                        .padding(.horizontal)

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

                Text("All Sets")
                    .font(.headline)
                    .padding(.horizontal)

                if historyEntries.isEmpty {
                    Text("No sets logged yet.")
                        .foregroundColor(.secondary)
                        .padding(.horizontal)
                } else {
                    ForEach(Array(historyEntries.enumerated()), id: \.offset) { _, entry in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(entry.date, style: .date)
                                Text(entry.date, style: .time)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                            Spacer()
                            Text("\(Int(entry.set.weight)) lb x \(entry.set.reps)")
                                .bold()
                        }
                        .padding(.horizontal)
                        .padding(.vertical, 4)
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
