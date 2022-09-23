import struct


def decode(fig, blob_id, scale):
    network = bytes(fig['blobs'][blob_id]['bytes'])

    i = 0
    num_vertices = struct.unpack('<I', network[i:i + 4])[0]
    i += 4
    num_segments = struct.unpack('<I', network[i:i + 4])[0]
    i += 4
    num_regions = struct.unpack('<I', network[i:i + 4])[0]
    i += 4

    vertices = []
    for vertex in range(num_vertices):
        # Should include stroke cap/limit, corner radius, mirroring, etc.
        style_id = struct.unpack('<I', network[i:i + 4])[0]

        # Coordinates
        x, y = struct.unpack('<ff', network[i + 4:i + 12])

        vertices.append(decode_vertex(x, y, scale))
        i += 12

    segments = []
    for segment in range(num_segments):
        # No idea what it's for
        style_id = struct.unpack('<I', network[i:i + 4])[0]

        # Start vertex + tangent vector
        v1 = struct.unpack('<I', network[i + 4:i + 8])[0]
        t1x, t1y = struct.unpack('<ff', network[i + 8:i + 16])

        # End vertex + tangent vector
        v2 = struct.unpack('<I', network[i + 16:i + 20])[0]
        t2x, t2y = struct.unpack('<ff', network[i + 20:i + 28])

        segments.append(decode_segment(v1, v2, t1x, t1y, t2x, t2y, scale))
        i += 28

    regions = []
    for region in range(num_regions):
        # Flags should include winding rule
        flags, num_loops = struct.unpack('<II', network[i:i + 8])
        i += 8

        loops = []
        for loop in range(num_loops):
            num_loop_vertices = struct.unpack('<I', network[i:i + 4])[0]
            i += 4

            loop_vertices = []
            for vertex in range(num_loop_vertices):
                loop_vertices.append(struct.unpack('<I', network[i:i + 4])[0])
                i += 4
            loops.append(loop_vertices)

        regions.append({'loops': loops})

    return {
        'regions': regions,
        'segments': segments,
        'vertices': vertices
    }


def decode_vertex(x, y, scale):
    return {
        'x': x / scale['x'],
        'y': y / scale['y']
    }


def decode_segment(v1, v2, t1x, t1y, t2x, t2y, scale):
    return {
        'start': v1,
        'end': v2,
        'tangentStart': {'x': t1x / scale['x'], 'y': t1y / scale['y']},
        'tangentEnd': {'x': t2x / scale['x'], 'y': t2y / scale['y']}
    }
