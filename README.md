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
