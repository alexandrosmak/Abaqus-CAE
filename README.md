# Abaqus-CAE

## Abaqus/Explicit VUSDFLD Subroutine (PEEQ + PEEQR)
### Overview
This repository contains a Fortran user subroutine for Abaqus/Explicit: VUSDFLD.
The subroutine reads two internal Abaqus variables at each material point in the current block:
PEEQ — equivalent (cumulative) plastic strain
PEEQR — equivalent plastic strain rate

It then stores these values into:
* State variables (STATEV) via STATENEW
* Field variables (FIELD) via the FIELD array

This makes PEEQ and PEEQR available for post-processing, output requests, or for driving field-dependent material behavior.

### Notes on implementation details
The code uses MAXBLK from VABA_PARAM.INC to dimension working arrays safely for vectorized execution.
It defines NRDATA_PEEQ = 1, meaning one value requested per block entry per VGETVRM call.
Separate buffers are used for PEEQ and PEEQR:
* RDATA_PEEQ
* RDATA_PEEQR
This prevents the second VGETVRM call from overwriting the first result.

### Compile and run Abaqus/Explicit with the user subroutine
abaqus job=JOB_NAME user=VUSDFLD_Final.f double interactive


## Abaqus Batch Runners
---

### EDP_Comp.py — Abaqus/Explicit Compression Batch Runner (INP Generator)
1. Reading a known-working **base `.inp`** file.
2. Removing the last `*Step ... *End Step` block.
3. Writing new `.inp` files, each with:
   - a selected **amplitude** name (e.g., `AMP-001`)
   - a corresponding **simulation time**
4. Submitting each generated input file using the Abaqus command line.
5. Renaming the resulting `.odb` file so it includes the amplitude tag.

This is useful when you want to re-run the same model with different loading rates/time scales controlled via amplitude definitions.

##### Configuration (edit at top of file):
Update these values in the **User parameters** section:
- `base_file`  
  Absolute path to a working base `.inp` file.
- `amplitudes`  
  List of amplitude names that must already exist/be referenced correctly in your base model.
- `simulation_times`  
  Step time associated with each amplitude (must match list length).
  - `user_sub` *(optional)*  
  Path to a user subroutine file (e.g., `VUSDFLD_Final.f`).  
  Leave empty (`""`) to run without a user subroutine.

#### How it works internally
- Reads the base `.inp`
- Locates the last `*Step` ... `*End Step` section
- Keeps everything *before* that block as common content
- Appends a newly built Step block for each run
- Submits via:
  - `abaqus job=<job_name> input=<short_path_to_inp>`


### EDP_Shear.py — Abaqus/Explicit Random Shear Batch Runner (INP Generator)

1. Reading a known-working **base `.inp`** file.  
2. Removing the last `*Step ... *End Step` block.  
3. Writing new `.inp` files, each with:
   - a selected **amplitude** name (e.g., `AMP-001`)
   - a corresponding **simulation time**
4. Submitting each generated input file using the Abaqus command line.  
5. Renaming the resulting `.odb` file so it includes the amplitude tag.  

This is useful when you want to re-run the same shear model with different loading histories / durations controlled via amplitude definitions (and optionally a user subroutine).

#### Configuration (edit at top of file):
Update these values in the **User parameters** section:
- `base_file`  
  Absolute path to a working base `.inp` file (e.g., `RandomExplicitShear.inp`).
- `amplitudes`  
  List of amplitude names that must already exist / be referenced correctly in your base model.
- `simulation_times`  
  Step time associated with each amplitude (must match list length).
- `user_sub` *(optional)*  
  Path to a user subroutine file (e.g., `VUSDFLD_Final.f`).  
  Leave empty (`""`) to run without a user subroutine.

#### How it works internally
- Reads the base `.inp`
- Locates the last `*Step` ... `*End Step` section
- Keeps everything *before* that block as common content
- Appends a newly built Explicit Step block for each run
- Applies shear boundary conditions using the selected amplitude
- Submits jobs via:
  - `abaqus job=<job_name> input=<short_path_to_inp>`




