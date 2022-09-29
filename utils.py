import uuid
import hashlib
import random
import struct

CURVE_MODES = {
    'STRAIGHT': 1,
    'ANGLE_AND_LENGTH': 2,
    'ANGLE': 3,
    'NONE': 4
}

id_salt = random.randbytes(16)


def gen_object_id(figma_id, suffix=b''):
    # Generate UUIDs by hashing the figma ID with a salt
    salted_id = id_salt + struct.pack('<II', *figma_id) + suffix
    uuid_bytes = bytearray(hashlib.shake_128(salted_id).digest(16))

    # Override bits to match UUIDv4
    uuid_bytes[6] = (uuid_bytes[6] & 0x0f) | 0x40
    uuid_bytes[8] = (uuid_bytes[8] & 0x3f) | 0x80

    return str(uuid.UUID(bytes=bytes(uuid_bytes))).upper()


def make_point(figma_node, x, y, figma_point={}):
    return {
        '_class': 'curvePoint',
        'cornerRadius': adjust_corner_radius(figma_node, figma_point),
        'curveFrom': '{0, 0}',
        'curveMode': adjust_curve_mode(figma_point, 'STRAIGHT'),
        'curveTo': '{0, 0}',
        'hasCurveFrom': False,
        'hasCurveTo': False,
        'point': f'{{{x}, {y}}}'
    }


def adjust_curve_mode(figma_point, default_value):
    if 'style' in figma_point and 'handleMirroring' in figma_point['style']:
        return CURVE_MODES[figma_point['style']['handleMirroring']]

    return CURVE_MODES[default_value]


def adjust_corner_radius(figma_node, figma_point):
    if 'style' in figma_point and 'cornerRadius' in figma_point['style']:
        return figma_point['style']['cornerRadius']

    return figma_node['cornerRadius']


def generate_file_ref(data):
    return hashlib.sha1(hashlib.sha1(data).digest()).hexdigest()


def add_points(point1, point2):
    return {'x': point1['x'] + point2['x'], 'y': point1['y'] + point2['y']}


def np_point_to_string(point):
    return f"{{{point[0]}, {point[1]}}}"


def point_to_string(point):
    return f"{{{point['x']}, {point['y']}}}"


# TODO: Call this function from every shape/image/etc
# TODO: Check if image masks work
def masking(figma):
    CLIPPING_MODE = {
        'ALPHA': 1,
        'OUTLINE': 0,  # TODO This works differently in Sketch vs Figma
        # Sketch masks only the fill and draws border normally and fill as background
        # Figma masks including the borders and ignores the stroke/fill properties
        # 'LUMINANCE': UNSUPPORTED
    }
    sketch = {
        'shouldBreakMaskChain': False
    }
    if figma.mask:
        sketch['hasClippingMask'] = True
        sketch['clippingMaskMode'] = CLIPPING_MODE[figma.maskType]
    else:
        sketch['hasClippingMask'] = False

    return sketch


def resizing_constraints(figma_item):
    # TODO: Figma is returning MIN so I assigned it to the defaults (TOP & LEFT respectively)
    v = {
        'MIN': 32,
        'BOTTOM': 8,
        'CENTER': 16,
        'TOP_BOTTOM': 40,
        'SCALE': 0,
    }
    h = {
        'MIN': 4,
        'RIGHT': 1,
        'CENTER': 2,
        'LEFT_RIGHT': 5,
        'SCALE': 0,
    }
    return h[figma_item['horizontalConstraint']] + v[figma_item['verticalConstraint']]


def get_style_table_override(figma_item):
    override_table = {0: {}}

    if 'styleOverrideTable' in figma_item:
        override_table.update({s['styleID']: s for s in figma_item['styleOverrideTable']})

    return override_table
