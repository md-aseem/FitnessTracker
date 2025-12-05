// input row
import SwiftUI

struct SetInputRow: View {
    @Binding var weightText: String
    @Binding var repsText: String

    var onAdd: () -> Void

    var body: some View {
        HStack {
            TextField("Weight", text: $weightText)
                .keyboardType(.decimalPad)
                .textFieldStyle(.roundedBorder)
                .frame(width: 90)

            Text("kg")

            TextField("Reps", text: $repsText)
                .keyboardType(.numberPad)
                .textFieldStyle(.roundedBorder)
                .frame(width: 80)

            Spacer()

            Button(action: onAdd) {
                Image(systemName: "plus.circle.fill")
                    .imageScale(.large)
            }
            .disabled(!canAdd)
        }
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
        repsText: .constant("8"),
        onAdd: { }
    )
    .padding()
}
