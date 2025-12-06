// settings
import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var workoutStore: WorkoutStore
    @State private var showingShareSheet = false
    @State private var shareItems: [Any] = []
    
    var body: some View {
        NavigationStack {
            List {
                Section {
                    Button {
                        exportCSV()
                    } label: {
                        Label {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Export Workouts")
                                    .foregroundStyle(.primary)
                                Text("CSV format for spreadsheets")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        } icon: {
                            Image(systemName: "tablecells")
                                .foregroundStyle(.green)
                        }
                    }
                    
                    Button {
                        exportJSON()
                    } label: {
                        Label {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Export Full Backup")
                                    .foregroundStyle(.primary)
                                Text("JSON format with all data")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        } icon: {
                            Image(systemName: "doc.badge.arrow.up")
                                .foregroundStyle(.blue)
                        }
                    }
                } header: {
                    Text("Export Data")
                } footer: {
                    Text("CSV includes workout history only. Full backup includes exercises and workouts for data restoration.")
                }
                
                Section {
                    HStack {
                        Text("Workouts")
                        Spacer()
                        Text("\(workoutStore.workouts.count)")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("Exercises")
                        Spacer()
                        Text("\(workoutStore.exercises.count)")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Text("Total Sets")
                        Spacer()
                        Text("\(totalSets)")
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Statistics")
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showingShareSheet) {
                ShareSheet(items: shareItems)
            }
        }
    }
    
    private var totalSets: Int {
        workoutStore.workouts.reduce(0) { $0 + $1.sets.count }
    }
    
    private func exportCSV() {
        let csv = workoutStore.exportWorkoutsToCSV()
        
        // Create a temporary file
        let fileName = "workouts_\(formattedDate()).csv"
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
        
        do {
            try csv.write(to: tempURL, atomically: true, encoding: .utf8)
            shareItems = [tempURL]
            showingShareSheet = true
        } catch {
            print("Error creating CSV file: \(error)")
        }
    }
    
    private func exportJSON() {
        guard let jsonData = workoutStore.exportFullDataToJSON() else { return }
        
        // Create a temporary file
        let fileName = "fitness_backup_\(formattedDate()).json"
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(fileName)
        
        do {
            try jsonData.write(to: tempURL)
            shareItems = [tempURL]
            showingShareSheet = true
        } catch {
            print("Error creating JSON file: \(error)")
        }
    }
    
    private func formattedDate() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }
}

// UIKit Share Sheet wrapper for SwiftUI
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

#Preview {
    SettingsView()
        .environmentObject(WorkoutStore())
}
