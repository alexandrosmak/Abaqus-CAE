import os
import ctypes
import subprocess
import time

# -----------------------------------------------------------------------------
# User parameters
# -----------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
base_file = os.path.join(repo_root, 'examples', 'input_files', 'Shear_Job.inp')
output_dir = os.path.join(repo_root, 'runs', 'shear')
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

amplitudes = ["AMP-001", "AMP-01", "AMP-025", "AMP-05"]
simulation_times = [32.331, 3.233, 1.293, 0.647]
user_sub = ''  # Set to path of user subroutine or leave empty

# -----------------------------------------------------------------------------
# Helper to get short (8.3) Windows path
# -----------------------------------------------------------------------------
def get_short_path(path):
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetShortPathNameW(path, buffer, 260)
    return buffer.value

# -----------------------------------------------------------------------------
# Read original INP and strip existing Step block
# -----------------------------------------------------------------------------
if not os.path.exists(base_file):
    raise FileNotFoundError("Input file not found: {}".format(base_file))

with open(base_file, 'r') as f:
    lines = f.readlines()

# Locate last *Step ... *End Step
step_start = None
step_end = None
for idx in range(len(lines)-1, -1, -1):
    tag = lines[idx].strip().lower()
    if tag.startswith('*end step') and step_end is None:
        step_end = idx
    elif tag.startswith('*step') and step_end is not None:
        step_start = idx
        break

if step_start is None or step_end is None:
    raise RuntimeError("Could not find *Step / *End Step sections in the input file.")

common_content = lines[:step_start]

# -----------------------------------------------------------------------------
# Generate new INP files for each amplitude/time
# -----------------------------------------------------------------------------
created_jobs = []
for amp, sim_time in zip(amplitudes, simulation_times):
    new_step = [
        "** STEP: Step-1\n",
        "*Step, name=Step-1, nlgeom=YES\n",
        "*Dynamic, Explicit, scale factor=0.1\n",
        ", {}\n".format(sim_time),
        "*Bulk Viscosity\n",
        "0.06, 1.2\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PICKEDSET8, 1, 1, 1.\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PICKEDSET8, 2, 2\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PICKEDSET8, 3, 3\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PICKEDSET8, 4, 4\n",
        "*Boundary, amplitude={}\n".format(amp),
        "_PICKEDSET8, 5, 5\n",
        "*Restart, write, number interval=1, time marks=NO\n",
        "*Output, field\n",
        "*Node Output\n",
        "A, RF, U, V\n",
        "*Element Output, directions=YES\n",
        "ER, EVF, FV, LE, PE, PEEQ, PEEQVAVG, PEVAVG, S, SDV, SVAVG\n",
        "*Contact Output\n",
        "CSTRESS,\n",
        "*Output, history, frequency=1\n",
        "*Energy Output\n",
        "ALLAE, ALLCD, ALLDMD, ALLFD, ALLIE, ALLKE, ALLPD, ALLSE, ALLVD, ALLWK, ETOTAL\n",
        "*Incrementation Output\n",
        "DT,\n",
        "*End Step\n"
    ]

    job_name = "Random_Shear_" + amp
    inp_name = job_name + ".inp"
    out_path = os.path.join(output_dir, inp_name)

    with open(out_path, 'w') as fo:
        fo.writelines(common_content + new_step)

    created_jobs.append((out_path, amp, job_name, inp_name))
    print("Created INP: {}".format(out_path))

# -----------------------------------------------------------------------------
# Submit each generated INP in the same directory and rename ODB
# -----------------------------------------------------------------------------
for inp_path, amp, job_name, inp_name in created_jobs:
    cwd = output_dir
    inp_short = get_short_path(inp_path)

    cmd = "abaqus job={} input={}".format(job_name, inp_short)
    if user_sub:
        cmd = cmd + " user=" + get_short_path(user_sub)

    print("Submitting: '{}' in {}".format(cmd, cwd))
    rc = subprocess.call(cmd, shell=True, cwd=cwd)
    if rc != 0:
        print("Job {} failed with return code {}".format(job_name, rc))
        continue

    time.sleep(3)
    odb_src = os.path.join(cwd, job_name + ".odb")
    odb_dst = os.path.join(cwd, "Random_Shear_{}.odb".format(amp))
    if os.path.exists(odb_src):
        os.rename(odb_src, odb_dst)
        print("Renamed ODB to: {}".format(odb_dst))
    else:
        print("Warning: ODB not found for job {}".format(job_name))
