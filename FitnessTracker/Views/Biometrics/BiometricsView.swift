
import SwiftUI

struct BiometricsView: View {
    @EnvironmentObject var store: WorkoutStore
    @State private var showingAddMetric = false
    @State private var newMetricName = ""
    @State private var newMetricUnit: BiometricUnit = .lbs
    
    var body: some View {
        NavigationStack {
            List {
                ForEach(store.biometricMetrics) { metric in
                    NavigationLink(destination: BiometricDetailView(metric: metric)) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(metric.name)
                                    .font(.headline)
                            }
                            
                            Spacer()
                            
                            if let latest = store.latestEntry(for: metric) {
                                VStack(alignment: .trailing) {
                                    Text("\(latest.value, specifier: "%.1f") \(metric.unit.rawValue)")
                                        .font(.body)
                                        .fontWeight(.medium)
                                    Text(latest.date, format: .dateTime.month().day())
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            } else {
                                Text("No data")
                                    .foregroundStyle(.secondary)
                                    .font(.caption)
                            }
                        }
                    }
                }
                .onDelete { indexSet in
                    indexSet.forEach { index in
                        store.deleteBiometricMetric(store.biometricMetrics[index])
                    }
                }
            }
            .navigationTitle("Biometrics")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingAddMetric = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddMetric) {
                NavigationStack {
                    Form {
                        TextField("Name", text: $newMetricName)
                        Picker("Unit", selection: $newMetricUnit) {
                            ForEach(BiometricUnit.allCases, id: \.self) { unit in
                                Text(unit.rawValue).tag(unit)
                            }
                        }
                    }
                    .navigationTitle("New Metric")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Cancel") { showingAddMetric = false }
                        }
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Add") {
                                store.addBiometricMetric(name: newMetricName, unit: newMetricUnit)
                                newMetricName = ""
                                showingAddMetric = false
                            }
                            .disabled(newMetricName.isEmpty)
                        }
                    }
                }
                .presentationDetents([.medium])
            }
        }
    }
}
