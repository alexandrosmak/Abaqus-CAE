# Abaqus/CAE script: convert an existing shell mesh part into a solid mesh part
# ---------------------------------------------------------------------------
# This script only performs the mesh conversion inside Abaqus/CAE.
# It does not edit steps, contacts, materials, sections, boundary conditions,
# loads, amplitudes, output requests, or assembly instances.
#
# Typical use in Abaqus/CAE:
#   File -> Run Script -> select this file
#
# Or from the command line:
#   abaqus cae noGUI=scripts/cae/shell_to_solid_part.py
#
# After running, inspect the new part visually, assign a solid section manually,
# create or adjust the assembly instance manually, then export the input file.

from abaqus import *
from abaqusConstants import *
import mesh
import math


# ---------------- USER SETTINGS ----------------
MODEL_NAME = None                  # None selects the first model in the CAE database
SOURCE_PART_NAME = 'SOURCE_PART'   # Existing shell-mesh part
NEW_PART_NAME = 'SOURCE_PART_SOLID'
TOTAL_THICKNESS = 1.0              # Total wall thickness in current model units
LAYERS = 2                         # Number of solid elements through thickness
REVERSE_NORMAL = False             # True flips the offset direction
SOLID_ELEM_CODE = C3D8R
SOLID_ELEM_LIBRARY = EXPLICIT
# ------------------------------------------------


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vnorm(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def vunit(a):
    n = vnorm(a)
    if n < 1.0e-20:
        return (0.0, 0.0, 1.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def get_model(model_name):
    if not mdb.models.keys():
        raise RuntimeError('No models found in the current Abaqus/CAE database.')
    if model_name is None:
        model_name = mdb.models.keys()[0]
    if model_name not in mdb.models.keys():
        raise RuntimeError('Model not found: %s' % model_name)
    return mdb.models[model_name]


def detect_connectivity_mode(src, node_coords):
    raw_conns = [list(e.connectivity) for e in src.elements]
    if not raw_conns:
        raise RuntimeError('Source part has no elements.')

    flat_conn = []
    for conn in raw_conns[:min(len(raw_conns), 200)]:
        flat_conn.extend(conn)

    if 0 in flat_conn:
        return True
    return not all((c in node_coords) for c in flat_conn)


def make_connectivity_converter(src, node_coords, connectivity_is_index):
    def conn_to_label(c):
        if connectivity_is_index:
            if c < 0 or c >= len(src.nodes):
                raise RuntimeError('Connectivity index out of range: %s' % str(c))
            return src.nodes[c].label
        if c not in node_coords:
            raise RuntimeError('Connectivity node label not found: %s' % str(c))
        return c
    return conn_to_label


def collect_quad_shell_elements(src, conn_to_label):
    quad_shell_elements = []
    skipped = 0
    for elem in src.elements:
        conn = [conn_to_label(c) for c in list(elem.connectivity)]
        if len(conn) == 4:
            quad_shell_elements.append((elem.label, conn))
        else:
            skipped += 1

    if not quad_shell_elements:
        raise RuntimeError('No 4-node shell elements found. This script converts quads only.')

    if skipped:
        print('Warning: skipped %d non-quad shell elements.' % skipped)

    return quad_shell_elements


def calculate_nodal_normals(node_labels, node_coords, quad_shell_elements, reverse_normal):
    nodal_normal_sum = dict((label, (0.0, 0.0, 0.0)) for label in node_labels)

    for old_elem_label, conn in quad_shell_elements:
        p1 = node_coords[conn[0]]
        p2 = node_coords[conn[1]]
        p4 = node_coords[conn[3]]
        normal = vunit(vcross(vsub(p2, p1), vsub(p4, p1)))
        if reverse_normal:
            normal = vscale(normal, -1.0)
        for label in conn:
            nodal_normal_sum[label] = vadd(nodal_normal_sum[label], normal)

    nodal_normals = {}
    for label in node_labels:
        nodal_normals[label] = vunit(nodal_normal_sum[label])

    return nodal_normals


def create_solid_part(model, new_part_name, node_labels, node_coords, nodal_normals,
                      quad_shell_elements, total_thickness, layers):
    if new_part_name in model.parts.keys():
        del model.parts[new_part_name]

    solid = model.Part(name=new_part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)

    new_node = {}
    next_node_label = 1
    for layer in range(layers + 1):
        offset = total_thickness * float(layer) / float(layers)
        for old_label in node_labels:
            x0 = node_coords[old_label]
            normal = nodal_normals[old_label]
            x = vadd(x0, vscale(normal, offset))
            solid.Node(coordinates=x, label=next_node_label)
            new_node[(old_label, layer)] = solid.nodes[-1]
            next_node_label += 1

    next_elem_label = 1
    for old_elem_label, conn in quad_shell_elements:
        for layer in range(layers):
            nodes = (new_node[(conn[0], layer)],
                     new_node[(conn[1], layer)],
                     new_node[(conn[2], layer)],
                     new_node[(conn[3], layer)],
                     new_node[(conn[0], layer + 1)],
                     new_node[(conn[1], layer + 1)],
                     new_node[(conn[2], layer + 1)],
                     new_node[(conn[3], layer + 1)])
            solid.Element(nodes=nodes, elemShape=HEX8, label=next_elem_label)
            next_elem_label += 1

    solid.setElementType(
        regions=(solid.elements,),
        elemTypes=(mesh.ElemType(elemCode=SOLID_ELEM_CODE, elemLibrary=SOLID_ELEM_LIBRARY),)
    )

    return solid


def convert_shell_part_to_solid(model_name, source_part_name, new_part_name,
                                total_thickness, layers, reverse_normal):
    if layers < 1:
        raise RuntimeError('LAYERS must be >= 1')
    if total_thickness <= 0.0:
        raise RuntimeError('TOTAL_THICKNESS must be > 0')

    model = get_model(model_name)

    if source_part_name not in model.parts.keys():
        raise RuntimeError('Source part not found: %s' % source_part_name)

    src = model.parts[source_part_name]

    node_coords = {}
    node_labels = []
    for node in src.nodes:
        node_coords[node.label] = tuple(node.coordinates)
        node_labels.append(node.label)
    node_labels.sort()

    connectivity_is_index = detect_connectivity_mode(src, node_coords)
    print('Detected connectivity mode: %s' % (
        'ZERO-BASED NODE INDICES' if connectivity_is_index else 'NODE LABELS'
    ))

    conn_to_label = make_connectivity_converter(src, node_coords, connectivity_is_index)
    quad_shell_elements = collect_quad_shell_elements(src, conn_to_label)
    nodal_normals = calculate_nodal_normals(
        node_labels, node_coords, quad_shell_elements, reverse_normal
    )

    solid = create_solid_part(
        model, new_part_name, node_labels, node_coords, nodal_normals,
        quad_shell_elements, total_thickness, layers
    )

    print('Created solid part: %s' % new_part_name)
    print('Source shell part: %s' % source_part_name)
    print('Converted quad shell elements: %d' % len(quad_shell_elements))
    print('Solid nodes: %d' % len(solid.nodes))
    print('Solid elements: %d' % len(solid.elements))
    print('Total thickness: %g, layers: %d, layer spacing: %g' % (
        total_thickness, layers, total_thickness / float(layers)
    ))
    print('Inspect offset direction. If needed, set REVERSE_NORMAL=True and rerun.')
    print('No other model definitions were modified.')

    return solid


convert_shell_part_to_solid(
    MODEL_NAME,
    SOURCE_PART_NAME,
    NEW_PART_NAME,
    TOTAL_THICKNESS,
    LAYERS,
    REVERSE_NORMAL
)
