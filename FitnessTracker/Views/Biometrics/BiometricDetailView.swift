
import SwiftUI
import Charts

struct BiometricDetailView: View {
    @EnvironmentObject var store: WorkoutStore
    let metric: BiometricMetric
    @State private var showingAddEntry = false
    
    var body: some View {
        List {
            Section {
                if !entries.isEmpty {
                    Chart {
                        ForEach(entries) { entry in
                            LineMark(
                                x: .value("Date", entry.date),
                                y: .value("Value", entry.value)
                            )
                            .foregroundStyle(Color.blue)
                            .interpolationMethod(.catmullRom)
                            
                            PointMark(
                                x: .value("Date", entry.date),
                                y: .value("Value", entry.value)
                            )
                            .foregroundStyle(Color.blue)
                        }
                    }
                    .frame(height: 200)
                    .padding(.vertical)
                } else {
                    Text("No data yet")
                        .foregroundStyle(.secondary)
                        .frame(height: 200)
                        .frame(maxWidth: .infinity)
                }
            } header: {
                Text("Progress")
            }
            
            Section {
                ForEach(entries.sorted(by: { $0.date > $1.date })) { entry in
                    HStack {
                        VStack(alignment: .leading) {
                            Text("\(entry.value, specifier: "%.1f") \(metric.unit.rawValue)")
                                .font(.headline)
                            if let note = entry.note {
                                Text(note)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        
                        Spacer()
                        
                        Text(entry.date, format: .dateTime.month().day().year())
                            .foregroundStyle(.secondary)
                    }
                    .swipeActions {
                        Button(role: .destructive) {
                            store.deleteBiometricEntry(entry)
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                }
            } header: {
                Text("History")
            }
        }
        .navigationTitle(metric.name)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showingAddEntry = true
                } label: {
                    Image(systemName: "plus")
                }
            }
        }
        .sheet(isPresented: $showingAddEntry) {
            AddBiometricEntryView(metric: metric)
        }
    }
    
    private var entries: [BiometricEntry] {
        store.entries(for: metric)
    }
}
