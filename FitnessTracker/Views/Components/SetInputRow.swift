// input row
import SwiftUI

struct SetInputRow: View {
    @Binding var weightText: String
    @Binding var repsText: String



    var body: some View {
        HStack(spacing: 12) {
            Spacer()

            TextField("Weight", text: $weightText)
                .keyboardType(.decimalPad)
                .textFieldStyle(.roundedBorder)
                .frame(width: 90)
                .multilineTextAlignment(.center)

            Text("lb")
                .foregroundColor(.secondary)

            TextField("Reps", text: $repsText)
                .keyboardType(.numberPad)
                .textFieldStyle(.roundedBorder)
                .frame(width: 80)
                .multilineTextAlignment(.center)

            Spacer()
        }
        .padding(.vertical, 8)
    }

    private var canAdd: Bool {
        if Double(weightText) ?? 0 <= 0 { return false }
        if Int(repsText) ?? 0 <= 0 { return false }
        return true
    }
}

#Preview {
    SetInputRow(
        weightText: .constant("60"),
        repsText: .constant("8")
    )
    .padding()
}
