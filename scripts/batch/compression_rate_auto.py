import os
import ctypes
import subprocess
import time

# -----------------------------------------------------------------------------
# User parameters
# -----------------------------------------------------------------------------
# Base INP file and output directory
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
base_file = os.path.join(repo_root, 'examples', 'input_files', 'Comp_Job.inp')
output_dir = os.path.join(repo_root, 'runs', 'compression')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Amplitudes and corresponding simulation times
amplitudes       = ["AMP-001", "AMP-01", "AMP-025", "AMP-05"]
simulation_times = [25.49,      2.55,      1.02,      0.51]

def get_short_path(path):
    """Return 8.3 short path for a given path (Windows only)."""
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetShortPathNameW(path, buffer, 260)
    return buffer.value

# -----------------------------------------------------------------------------
# Read the original INP and extract common content before the Step block
# -----------------------------------------------------------------------------
if not os.path.exists(base_file):
    raise FileNotFoundError("Base INP file not found: {}".format(base_file))

with open(base_file, 'r') as f:
    lines = f.readlines()

# Find the last '*Step' ... '*End Step' block
step_start = None
step_end   = None
for i in range(len(lines) - 1, -1, -1):
    tag = lines[i].strip().lower()
    if tag.startswith('*end step') and step_end is None:
        step_end = i
    elif tag.startswith('*step') and step_end is not None:
        step_start = i
        break

if step_start is None or step_end is None:
    raise RuntimeError("Could not locate *Step / *End Step in base INP")

common_content = lines[:step_start]

# -----------------------------------------------------------------------------
# Generate new INP files with updated Step for each amplitude/time
# -----------------------------------------------------------------------------
created_files = []
for amp, sim_time in zip(amplitudes, simulation_times):
    # Build the new Step section
    new_step = [
        "** STEP: ExplicitDynamic\n",
        "*Step, name=ExplicitDynamic, nlgeom=YES\n",
        "*Dynamic, Explicit\n",
        ", {}\n".format(sim_time),
        "*Bulk Viscosity\n",
        "0.06, 1.2\n",
        "** BOUNDARY CONDITIONS\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PickedSet27, 2, 2, -1.\n",
        "** OUTPUT REQUESTS\n",
        "*Restart, write, number interval=1, time marks=NO\n",
        "*Output, field, variable=PRESELECT\n",
        "*Output, history, variable=PRESELECT\n",
        "*End Step\n"
    ]

    out_name = "1mm_Compression{}.inp".format(amp)
    out_path = os.path.join(output_dir, out_name)
    with open(out_path, 'w') as fo:
        fo.writelines(common_content + new_step)
    created_files.append((out_path, amp))
    print("Created: {}".format(out_path))

# -----------------------------------------------------------------------------
# Submit each generated INP via Abaqus and rename the resulting ODB file
# -----------------------------------------------------------------------------
for inp_file, amp in created_files:
    job_name = os.path.splitext(os.path.basename(inp_file))[0]
    inp_short = get_short_path(inp_file)

    # Construct the Abaqus command
    cmd = "abaqus job={} input={}".format(job_name, inp_short)
    print("Submitting: {}".format(cmd))

    # Run the job
    rc = subprocess.call(cmd, shell=True, cwd=output_dir)
    if rc != 0:
        print("Job {} failed with return code {}".format(job_name, rc))
        continue

    # Wait for ODB to be written
    time.sleep(5)

    # Rename the ODB to include amplitude tag
    odb_src  = os.path.join(output_dir, job_name + ".odb")
    odb_dst  = os.path.join(output_dir, "1mm_compression_{}.odb".format(amp))
    if os.path.exists(odb_src):
        try:
            os.rename(odb_src, odb_dst)
            print("Renamed ODB to {}".format(odb_dst))
        except Exception as e:
            print("Error renaming ODB: {}".format(str(e)))
    else:
        print("ODB not found for job {}".format(job_name))
