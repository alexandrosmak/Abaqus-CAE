from odbAccess import openOdb
import os
import csv

# Directory with ODB files
odb_dir = r'C:\Users\tm1621\OneDrive - Imperial College London\PhD Research Project\Constitutive Model\Calibration\Abaqus\VonMises Plasticity'

# ODB names use this pattern
amplitudes = ["AMP-001", "AMP-01", "AMP-025", "AMP-05"]

# Output data list
combined_rows = []

for amp in amplitudes:
    odb_name = "Random_Shear_{}.odb".format(amp)
    odb_path = os.path.join(odb_dir, odb_name)

    if not os.path.exists(odb_path):
        print("ODB not found:", odb_path)
        continue

    print("Processing:", odb_name)
    odb = openOdb(odb_path)
    step = odb.steps[odb.steps.keys()[0]]

    for frame_number, frame in enumerate(step.frames):
        try:
            le = frame.fieldOutputs['LE']
            s = frame.fieldOutputs['S']
        except KeyError:
            print("LE or S not found in frame", frame_number)
            continue

        le12 = abs(le.values[0].data[3])  
        s12  = abs(s.values[0].data[3])  

        combined_rows.append([amp, frame_number, le12, s12])

    odb.close()

# Save combined CSV
output_csv = os.path.join(odb_dir, "Random_Shear_Results.csv")
with open(output_csv, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(["Amplitude", "Frame", "LE12_abs", "S12_abs"])
    writer.writerows(combined_rows)

print("Saved combined CSV:", output_csv)
