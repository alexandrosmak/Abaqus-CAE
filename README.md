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
abaqus job=JOB_NAME user=VUSDFLD.for double interactive
