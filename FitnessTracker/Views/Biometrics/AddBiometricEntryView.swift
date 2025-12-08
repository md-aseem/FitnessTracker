
import SwiftUI

struct AddBiometricEntryView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var store: WorkoutStore
    
    let metric: BiometricMetric
    
    @State private var value: Double = 0
    @State private var date: Date = Date()
    @State private var note: String = ""
    @State private var valueString: String = "" // For text field input
    
    var body: some View {
        NavigationStack {
            Form {
                Section(header: Text("Details")) {
                    HStack {
                        Text("Value (\(metric.unit.rawValue))")
                        Spacer()
                        TextField("0.0", text: $valueString)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                    }
                    
                    DatePicker("Date", selection: $date, displayedComponents: [.date, .hourAndMinute])
                }
                
                Section(header: Text("Notes")) {
                    TextField("Optional note", text: $note)
                }
            }
            .navigationTitle("Log \(metric.name)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        saveEntry()
                    }
                    .disabled(Double(valueString) == nil)
                }
            }
            .onAppear {
                // Pre-fill with previous value if available, or just empty?
                // existing logic usually prefers empty for new entry, or maybe last value
                if let lastEntry = store.latestEntry(for: metric) {
                    valueString = String(format: "%.1f", lastEntry.value)
                }
            }
        }
    }
    
    private func saveEntry() {
        guard let valueDouble = Double(valueString) else { return }
        
        store.addBiometricEntry(
            metricId: metric.id,
            value: valueDouble,
            date: date,
            note: note.isEmpty ? nil : note
        )
        
        dismiss()
    }
}
