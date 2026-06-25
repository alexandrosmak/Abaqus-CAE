# Abaqus-CAE

Utilities, scripts, examples, and subroutines for Abaqus/CAE and
Abaqus/Explicit workflows.

## Repository Structure

```text
Abaqus-CAE/
  scripts/
    cae/
      shell_to_solid_part.py
    batch/
      compression_rate_auto.py
      shear_rate_auto.py
    extraction/
      compression_extract.py
      shear_extract.py
  subroutines/
    VUSFLD_Final.f
  examples/
    input_files/
      Comp_Job.inp
      Shear_Job.inp
    shell_to_solid_settings.py
  README.md
  .gitignore
```

Generated Abaqus run outputs are written to `runs/`, which is ignored by git.

## Abaqus/CAE Utilities

### `scripts/cae/shell_to_solid_part.py`

Generic Abaqus/CAE script for converting an existing 4-node shell mesh part into
a solid orphan-mesh part.

What it does:

1. Reads an existing shell mesh part from the open CAE database.
2. Computes averaged nodal normals from shell element connectivity.
3. Creates a new solid orphan-mesh part by offsetting shell nodes through the requested thickness.
4. Converts each quadrilateral shell element into layered C3D8R solid elements.

Edit the `USER SETTINGS` block before running:

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

After running, inspect the generated solid part, confirm the offset direction,
assign a solid section, update the assembly instance as needed, and export the
input file manually.

Notes:

- Converts 4-node quadrilateral shell elements only.
- Creates reduced-integration C3D8R brick elements by default.
- Does not modify steps, contacts, materials, sections, boundary conditions, loads, amplitudes, output requests, or assembly instances.
- If the solid wall grows in the wrong direction, set `REVERSE_NORMAL = True` and rerun.

## Batch Runners

### `scripts/batch/compression_rate_auto.py`

Generates and submits Abaqus/Explicit compression `.inp` files from
`examples/input_files/Comp_Job.inp`.

The script:

1. Reads the base input file.
2. Removes the last `*Step ... *End Step` block.
3. Writes one generated input file per amplitude and simulation time.
4. Submits each job through the Abaqus command line.
5. Renames each resulting `.odb` file with its amplitude tag.

Generated compression files are written to `runs/compression/`.

### `scripts/batch/shear_rate_auto.py`

Generates and submits Abaqus/Explicit shear `.inp` files from
`examples/input_files/Shear_Job.inp`.

The script:

1. Reads the base input file.
2. Removes the last `*Step ... *End Step` block.
3. Writes one generated input file per amplitude and simulation time.
4. Submits each job through the Abaqus command line.
5. Renames each resulting `.odb` file with its amplitude tag.

Generated shear files are written to `runs/shear/`.

## ODB Extraction

### `scripts/extraction/compression_extract.py`

Post-processes compression `.odb` files in `runs/compression/` and extracts:

- `LE22`: logarithmic strain in the 22 direction
- `S22`: Cauchy stress in the 22 direction

Absolute values are written to `Compression Results 1mm.csv`.

### `scripts/extraction/shear_extract.py`

Post-processes shear `.odb` files in `runs/shear/` and extracts:

- `LE12`: logarithmic shear strain
- `S12`: Cauchy shear stress

Absolute values are written to `Random_Shear_Results.csv`.

## User Subroutines

### `subroutines/VUSFLD_Final.f`

Fortran user subroutine for Abaqus/Explicit `VUSDFLD`.

The subroutine reads two internal Abaqus variables at each material point in the
current block:

- `PEEQ`: equivalent cumulative plastic strain
- `PEEQR`: equivalent plastic strain rate

It stores these values into:

- State variables through `STATENEW`
- Field variables through the `FIELD` array

Compile and run Abaqus/Explicit with:

```text
abaqus job=JOB_NAME user=subroutines/VUSFLD_Final.f double interactive
```

## Examples

- `examples/input_files/Comp_Job.inp`: base compression input deck.
- `examples/input_files/Shear_Job.inp`: base shear input deck.
- `examples/shell_to_solid_settings.py`: settings template for the CAE shell-to-solid utility.
