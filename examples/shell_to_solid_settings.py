# Copy these values into scripts/cae/shell_to_solid_part.py and replace
# the placeholders with names from your Abaqus/CAE model.

MODEL_NAME = None                  # None selects the first model in the CAE database
SOURCE_PART_NAME = 'SOURCE_PART'   # Existing shell-mesh part
NEW_PART_NAME = 'SOURCE_PART_SOLID'
TOTAL_THICKNESS = 1.0              # Use the same length units as the model
LAYERS = 2                         # Number of solid elements through thickness
REVERSE_NORMAL = False             # True flips the offset direction
