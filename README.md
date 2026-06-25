# Abaqus-CAE

Utilities, scripts, and subroutines for Abaqus/CAE and Abaqus/Explicit workflows.

## Repository Structure

```text
Abaqus-CAE/
  scripts/
    cae/
      shell_to_solid_part.py
  examples/
    shell_to_solid_settings.py
  README.md
  .gitignore
```

Recommended structure for future additions:

```text
  scripts/
    batch/        # INP generation and Abaqus job submission scripts
    extraction/   # ODB post-processing scripts
  subroutines/    # Fortran user subroutines such as VUSDFLD
```

## Abaqus/CAE Utilities

### `scripts/cae/shell_to_solid_part.py` - Shell-to-solid mesh conversion

Generic Abaqus/CAE script for converting an existing 4-node shell mesh part into a solid orphan-mesh part.

What it does:

1. Reads an existing shell mesh part from the open CAE database.
2. Computes averaged nodal normals from shell element connectivity.
3. Creates a new solid orphan-mesh part by offsetting shell nodes through the requested thickness.
4. Converts each quadrilateral shell element into layered C3D8R solid elements.

The script is model-agnostic. Edit the `USER SETTINGS` block before running:

```python
MODEL_NAME = None
SOURCE_PART_NAME = 'SOURCE_PART'
NEW_PART_NAME = 'SOURCE_PART_SOLID'
TOTAL_THICKNESS = 1.0
LAYERS = 2
REVERSE_NORMAL = False
```

Run from Abaqus/CAE:

```text
File -> Run Script -> scripts/cae/shell_to_solid_part.py
```

Or from the command line:

```text
abaqus cae noGUI=scripts/cae/shell_to_solid_part.py
```

After running, inspect the generated solid part, confirm the offset direction, assign a solid section, update the assembly instance as needed, and export the input file manually.

Notes:

- Converts 4-node quadrilateral shell elements only.
- Creates reduced-integration C3D8R brick elements by default.
- Does not modify steps, contacts, materials, sections, boundary conditions, loads, amplitudes, output requests, or assembly instances.
- If the solid wall grows in the wrong direction, set `REVERSE_NORMAL = True` and rerun.

## Abaqus/Explicit VUSDFLD Subroutine

### Overview

This repository also documents a Fortran user subroutine for Abaqus/Explicit: `VUSDFLD`.

The subroutine reads two internal Abaqus variables at each material point in the current block:

- `PEEQ`: equivalent cumulative plastic strain
- `PEEQR`: equivalent plastic strain rate

It then stores these values into:

- State variables through `STATENEW`
- Field variables through the `FIELD` array

This makes `PEEQ` and `PEEQR` available for post-processing, output requests, or field-dependent material behavior.

### Notes on implementation details

The code uses `MAXBLK` from `VABA_PARAM.INC` to dimension working arrays safely for vectorized execution.

It defines `NRDATA_PEEQ = 1`, meaning one value is requested per block entry per `VGETVRM` call. Separate buffers are used for `PEEQ` and `PEEQR`:

- `RDATA_PEEQ`
- `RDATA_PEEQR`

This prevents the second `VGETVRM` call from overwriting the first result.

### Compile and run Abaqus/Explicit with the user subroutine

```text
abaqus job=JOB_NAME user=VUSDFLD_Final.f double interactive
```

## Abaqus Batch Runners

### `EDP_Comp.py` - Abaqus/Explicit compression batch runner

This script generates and submits compression `.inp` files from a known-working base input file.

It is intended to:

1. Read a base `.inp` file.
2. Remove the last `*Step ... *End Step` block.
3. Write new `.inp` files with selected amplitude names and simulation times.
4. Submit each generated input file using the Abaqus command line.
5. Rename each resulting `.odb` file so it includes the amplitude tag.

Configuration values to edit at the top of the file:

- `base_file`: absolute path to a working base `.inp` file.
- `amplitudes`: amplitude names that already exist or are referenced correctly in the base model.
- `simulation_times`: step time for each amplitude. This must match the amplitude list length.
- `user_sub`: optional path to a user subroutine, such as `VUSDFLD_Final.f`. Leave empty to run without a user subroutine.

### `EDP_Shear.py` - Abaqus/Explicit random shear batch runner

This script generates and submits shear `.inp` files from a known-working base input file.

It is intended to:

1. Read a base `.inp` file.
2. Remove the last `*Step ... *End Step` block.
3. Write new `.inp` files with selected amplitude names and simulation times.
4. Submit jobs through Abaqus.
5. Rename each resulting `.odb` file so it includes the amplitude tag.

Configuration values to edit at the top of the file:

- `base_file`: absolute path to a working base `.inp` file.
- `amplitudes`: amplitude names that already exist or are referenced correctly in the base model.
- `simulation_times`: step time for each amplitude. This must match the amplitude list length.
- `user_sub`: optional path to a user subroutine, such as `VUSDFLD_Final.f`. Leave empty to run without a user subroutine.

## Abaqus Batch Extraction

### `Comp_Extract.py` - Abaqus ODB compression results extractor

Post-processes multiple Abaqus/Explicit compression `.odb` files and extracts:

- `LE22`: logarithmic strain in the 22 direction
- `S22`: Cauchy stress in the 22 direction

Absolute values are taken and written into a combined CSV file for all amplitudes.

### `Shear_Extract.py` - Abaqus ODB random shear results extractor

Post-processes multiple Abaqus/Explicit shear `.odb` files and extracts:

- `LE12`: logarithmic shear strain
- `S12`: Cauchy shear stress

Absolute values are taken and written into a combined CSV file for all amplitudes.
