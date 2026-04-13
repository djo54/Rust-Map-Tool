"""
Convertisseur de fichier .map Rust vers PNG
Format K4os.Compression.LZ4.Legacy + Protobuf WorldData
Version 2 - avec ocean, rivieres, routes et monuments
"""

import struct
import io
import os
import sys
import lz4.block
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ─── Couleurs de reference ────────────────────────────────────────────────────
OCEAN_COLOR       = (11,  58,  74)   # Teal fonce (reference)
OCEAN_DEEP_COLOR  = ( 8,  45,  60)   # Teal tres fonce (profond)
SHORE_COLOR       = (180, 200, 210)  # Rivage clair
RIVER_COLOR       = (25,  90, 140)   # Bleu riviere
ROAD_COLOR        = ( 40,  38,  35)  # Brun tres fonce route
RAIL_COLOR        = ( 55,  50,  50)  # Gris rail
POWERLINE_COLOR   = ( 60,  55,  40)  # Brun olive ligne electrique

# Couleurs monument par categorie
MONUMENT_COLORS = {
    'monument':    ((180, 130,  60), 7),   # Orange - grands monuments
    'dungeon':     ((130,  90,  60), 5),   # Brun - donjons
    'dungeonbase': ((100,  75,  55), 4),   # Brun fonce
    'decor':       None,                   # Decorations = pas dessine
}

# Couleurs splat (8 types de sol Rust: Dirt, Snow, Sand, Rock, Grass, Forest, Stones, Gravel)
SPLAT_RGB = np.array([
    [130, 108,  75],   # 0 Dirt       - terre
    [215, 225, 228],   # 1 Snow       - neige
    [200, 178, 105],   # 2 Sand       - sable
    [115, 105,  98],   # 3 Rock       - roche
    [ 95, 135,  65],   # 4 Grass      - herbe verte
    [ 55,  90,  45],   # 5 Forest     - foret sombre
    [150, 140, 130],   # 6 Stones     - pierres
    [125, 118, 108],   # 7 Gravel     - gravier
], dtype=np.float32)


# ─── Decompression K4os LZ4 Legacy Stream ────────────────────────────────────

def read_varint(stream):
    result = 0; shift = 0
    while True:
        b = stream.read(1)
        if not b: return None
        b = b[0]
        result |= (b & 0x7F) << shift
        shift += 7
        if not (b & 0x80): break
    return result

def decompress_k4os_lz4_stream(data):
    stream = io.BytesIO(data)
    result = io.BytesIO()
    chunk_count = 0
    while True:
        flags = read_varint(stream)
        if flags is None: break
        is_compressed = bool(flags & 1)
        original_length = read_varint(stream)
        if original_length is None: break
        compressed_length = read_varint(stream) if is_compressed else original_length
        if compressed_length is None: break
        chunk_data = stream.read(compressed_length)
        if len(chunk_data) < compressed_length: break
        if is_compressed:
            try:
                chunk = lz4.block.decompress(chunk_data, uncompressed_size=original_length)
            except Exception as e:
                print(f"  [ERREUR chunk {chunk_count}]: {e}")
                break
        else:
            chunk = chunk_data
        result.write(chunk)
        chunk_count += 1
        if chunk_count % 50 == 0:
            print(f"  -> {chunk_count} chunks, {result.tell()/1024/1024:.0f} MB...")
    print(f"  OK: {chunk_count} chunks, {result.tell()/1024/1024:.1f} MB decompresses")
    return result.getvalue()


# ─── Parsing Protobuf ─────────────────────────────────────────────────────────

def parse_varint_buf(data, pos):
    result = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift; shift += 7
        if not (b & 0x80): return result, pos
    return result, pos

def parse_float_buf(data, pos):
    val = struct.unpack_from('<f', data, pos)[0]
    return val, pos + 4

def parse_vector(data, start, end):
    x = y = z = 0.0
    pos = start
    while pos < end:
        tag, pos = parse_varint_buf(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 5:
            v, pos = parse_float_buf(data, pos)
            if fn == 1: x = v
            elif fn == 2: y = v
            elif fn == 3: z = v
        elif wt == 0: _, pos = parse_varint_buf(data, pos)
        elif wt == 2:
            ln, pos = parse_varint_buf(data, pos)
            pos += ln
        else: break
    return x, y, z

def parse_path_data(data, start, end):
    """Retourne (name, nodes_list, width) depuis un message PathData."""
    name = ''
    nodes = []
    width = 8.0
    pos = start
    while pos < end:
        try:
            tag, pos = parse_varint_buf(data, pos)
            fn = tag >> 3; wt = tag & 7
            if wt == 0:
                _, pos = parse_varint_buf(data, pos)
            elif wt == 5:
                v, pos = parse_float_buf(data, pos)
                if fn == 5: width = v  # PathData.width
            elif wt == 2:
                ln, pos = parse_varint_buf(data, pos)
                vstart = pos; pos += ln
                if fn == 1:
                    name = data[vstart:vstart+ln].decode('utf-8', errors='replace')
                elif fn == 15:  # repeated VectorData nodes
                    x, y, z = parse_vector(data, vstart, vstart+ln)
                    nodes.append((x, z))
            elif wt == 1:
                pos += 8
            else:
                break
        except Exception:
            break
    return name, nodes, width

def parse_prefab_data(data, start, end):
    """Retourne (id, category, pos_x, pos_z)."""
    pid = 0; category = ''; px = 0.0; pz = 0.0
    pos = start
    while pos < end:
        tag, pos = parse_varint_buf(data, pos)
        fn = tag >> 3; wt = tag & 7
        if wt == 0:
            v, pos = parse_varint_buf(data, pos)
            if fn == 2: pid = v
        elif wt == 2:
            ln, pos = parse_varint_buf(data, pos)
            vstart = pos; pos += ln
            if fn == 1:
                category = data[vstart:vstart+ln].decode('utf-8', errors='replace')
            elif fn == 3:  # position VectorData
                x, y, z = parse_vector(data, vstart, vstart+ln)
                px, pz = x, z
        else:
            # wire type 1 (64-bit) ou 5 (32-bit) - skip
            if wt == 1: pos += 8
            elif wt == 5: pos += 4
            else: break
    return pid, category, px, pz

def parse_world_data(proto_data):
    """Parse WorldData complet."""
    map_size = 0
    maps = {}
    paths = []
    prefabs = []
    pos = 0; total = len(proto_data)

    print(f"  Parsing protobuf ({total/1024/1024:.0f} MB)...")

    while pos < total:
        if pos + 1 >= total: break
        tag, pos = parse_varint_buf(proto_data, pos)
        fn = tag >> 3; wt = tag & 7

        if wt == 0:
            v, pos = parse_varint_buf(proto_data, pos)
            if fn == 1: map_size = v; print(f"  Map size: {map_size}m")
        elif wt == 2:
            length, pos = parse_varint_buf(proto_data, pos)
            start = pos; pos += length

            if fn == 2:  # MapData
                name = None; ldata = None; p2 = start
                while p2 < start + length:
                    t2, p2 = parse_varint_buf(proto_data, p2)
                    f2 = t2 >> 3; w2 = t2 & 7
                    if w2 == 2:
                        ln, p2 = parse_varint_buf(proto_data, p2)
                        v = proto_data[p2:p2+ln]; p2 += ln
                        if f2 == 1: name = v.decode('utf-8', errors='replace')
                        elif f2 == 2: ldata = v
                    else: _, p2 = parse_varint_buf(proto_data, p2)
                if name and ldata:
                    maps[name] = ldata
                    print(f"  Layer '{name}': {len(ldata)/1024/1024:.1f} MB")

            elif fn == 3:  # PrefabData
                prefabs.append(proto_data[start:start+length])

            elif fn == 4:  # PathData
                paths.append(proto_data[start:start+length])

        elif wt == 1: pos += 8
        elif wt == 5: pos += 4
        else: break

    print(f"  Prefabs: {len(prefabs)}, Paths: {len(paths)}")
    return map_size, maps, prefabs, paths


# ─── Decodage des couches ─────────────────────────────────────────────────────

def decode_heightmap(data):
    n = len(data) // 2
    side = int(n ** 0.5)
    arr = np.frombuffer(data[:side*side*2], dtype='<u2').reshape(side, side)
    return arr.astype(np.float32), side

def decode_splat_planes(data):
    """Decode splat: 8 plans de 2048x2048 uint8."""
    side = 2048
    plane = side * side
    planes = []
    for i in range(8):
        p = np.frombuffer(data[i*plane:(i+1)*plane], dtype=np.uint8)
        planes.append(p.reshape(side, side).astype(np.float32))
    return np.stack(planes, axis=2)  # (2048, 2048, 8)

def decode_topology(data):
    side = 2048
    arr = np.frombuffer(data[:side*side*4], dtype='<i4').reshape(side, side)
    return arr

def decode_biome_planes(data):
    """Decode biome: 5 plans de 2048x2048 uint8 (Arid, Temperate, Tundra, Arctic, extra)."""
    side = 2048
    plane = side * side
    # 4 premiers plans utilises
    planes = [np.frombuffer(data[i*plane:(i+1)*plane], dtype=np.uint8).reshape(side, side).astype(np.float32)
              for i in range(4)]
    return np.stack(planes, axis=2)  # (2048, 2048, 4) = Arid, Temperate, Tundra, Arctic


# ─── Rendu PNG ────────────────────────────────────────────────────────────────

def world_to_pixel(wx, wz, map_size, img_size):
    """Convertit coordonnees monde (-map/2..+map/2) vers pixels (0..img_size)."""
    px = int((wx + map_size / 2) / map_size * img_size)
    pz = int((wz + map_size / 2) / map_size * img_size)
    # Flip Y (Unity Z+ = nord = haut dans l'image)
    py = img_size - 1 - pz
    return px, py


def render_map_png(map_size, maps, prefabs_raw, paths_raw, output_path, out_size=None):
    available = list(maps.keys())
    print(f"\n  Couches: {available}")

    # ── Decoder les couches ───────────────────────────────────────────────────
    terrain_raw, t_side = decode_heightmap(maps['terrain'])
    water_raw, _        = decode_heightmap(maps['water'])
    topology_raw        = decode_topology(maps['topology'])
    splat_planes        = decode_splat_planes(maps['splat'])

    has_biome = 'biome' in maps
    if has_biome:
        biome_planes = decode_biome_planes(maps['biome'])
    else:
        biome_planes = None

    print(f"  Terrain: {t_side}x{t_side}, Topologie: {topology_raw.shape}")

    # ── Sea level depuis la couche eau ───────────────────────────────────────
    water_present = water_raw[water_raw > 0]
    sea_level = float(water_present.mean()) if len(water_present) > 0 else 16500.0
    print(f"  Niveau mer: {sea_level:.0f} raw")

    # ── Masque ocean depuis topologie (Lake bit 7 = 128) ────────────────────
    # Upsampler topologie 2048->t_side
    topo_ocean_2048 = (topology_raw & 128) != 0  # Lake flag = ocean/eau profonde
    topo_river_2048 = (topology_raw & 64) != 0   # Riverside flag
    topo_beach_2048 = (topology_raw & 32) != 0   # Beach flag

    # Upsampler vers resolution terrain
    scale = t_side / 2048
    from PIL import Image as PILImage
    topo_img = PILImage.fromarray(topo_ocean_2048.astype(np.uint8) * 255)
    topo_img = topo_img.resize((t_side, t_side), PILImage.NEAREST)
    ocean_mask = np.array(topo_img) > 127  # (t_side, t_side) bool

    topo_river_img = PILImage.fromarray(topo_river_2048.astype(np.uint8) * 255)
    topo_river_img = topo_river_img.resize((t_side, t_side), PILImage.NEAREST)
    river_topo_mask = np.array(topo_river_img) > 127

    topo_beach_img = PILImage.fromarray(topo_beach_2048.astype(np.uint8) * 255)
    topo_beach_img = topo_beach_img.resize((t_side, t_side), PILImage.NEAREST)
    beach_mask = np.array(topo_beach_img) > 127

    print(f"  Ocean (topologie Lake): {ocean_mask.sum()/t_side**2*100:.1f}%")

    # ── Normaliser terrain pour hillshading ──────────────────────────────────
    t_min = terrain_raw.min()
    t_max = terrain_raw.max()
    terrain_norm = (terrain_raw - t_min) / max(t_max - t_min, 1)

    # ── Canvas de rendu (float) ───────────────────────────────────────────────
    # Resolution de sortie (None = native)
    if out_size is None:
        out_size = t_side

    print(f"  Rendu {t_side}x{t_side} -> sortie {out_size}x{out_size}...")
    canvas = np.zeros((t_side, t_side, 3), dtype=np.float32)

    # ── Fond = ocean teal ────────────────────────────────────────────────────
    canvas[:, :, 0] = OCEAN_COLOR[0]
    canvas[:, :, 1] = OCEAN_COLOR[1]
    canvas[:, :, 2] = OCEAN_COLOR[2]

    # ── Colorer le terrain (zones terre seulement) ───────────────────────────
    land_mask = ~ocean_mask

    # Upsampler splat (2048->t_side)
    sp_img = PILImage.fromarray(splat_planes[:, :, 0].astype(np.uint8))
    sp_resized = np.zeros((t_side, t_side, 8), dtype=np.float32)
    for i in range(8):
        ch = PILImage.fromarray(splat_planes[:, :, i].astype(np.uint8))
        ch = ch.resize((t_side, t_side), PILImage.BILINEAR)
        sp_resized[:, :, i] = np.array(ch, dtype=np.float32)

    # Blend couleurs splat
    sp_sum = sp_resized.sum(axis=2, keepdims=True)
    sp_sum = np.where(sp_sum < 1, 1, sp_sum)
    sp_norm = sp_resized / sp_sum

    terrain_r = (sp_norm * SPLAT_RGB[:, 0]).sum(axis=2)
    terrain_g = (sp_norm * SPLAT_RGB[:, 1]).sum(axis=2)
    terrain_b_ch = (sp_norm * SPLAT_RGB[:, 2]).sum(axis=2)

    # Zones sans splat = fallback hauteur
    no_splat = (sp_resized.sum(axis=2) < 1.0)
    h_rel = terrain_norm
    terrain_r  = np.where(no_splat, 80 + h_rel * 60, terrain_r)
    terrain_g  = np.where(no_splat, 90 + h_rel * 50, terrain_g)
    terrain_b_ch = np.where(no_splat, 60 + h_rel * 40, terrain_b_ch)

    # ── Hillshading ──────────────────────────────────────────────────────────
    amp = 12.0
    dx = np.gradient(terrain_norm * amp, axis=1)
    dy = np.gradient(terrain_norm * amp, axis=0)
    lx, ly, lz = -0.707, -0.707, 1.0
    ln = (lx**2 + ly**2 + lz**2) ** 0.5
    lx /= ln; ly /= ln; lz /= ln
    nz = 1.0 / (1.0 + dx**2 + dy**2) ** 0.5
    nx = -dx * nz; ny = -dy * nz
    shade = nx * lx + ny * ly + nz * lz
    shade = np.clip(shade, 0, 1)
    shade = 0.65 + 0.35 * shade  # lumiere ambiante 65%, directionnelle 35%

    # Appliquer terrain sur les zones de terre
    lf = land_mask.astype(np.float32)
    canvas[:, :, 0] = canvas[:, :, 0] * (1 - lf) + terrain_r * shade * lf
    canvas[:, :, 1] = canvas[:, :, 1] * (1 - lf) + terrain_g * shade * lf
    canvas[:, :, 2] = canvas[:, :, 2] * (1 - lf) + terrain_b_ch * shade * lf

    # ── Eau douce (lacs/rivieres de la water layer) ──────────────────────────
    fresh_water = (water_raw > 0) & ~ocean_mask
    fw_f = fresh_water.astype(np.float32)
    canvas[:, :, 0] = canvas[:, :, 0] * (1 - fw_f) + RIVER_COLOR[0] * fw_f
    canvas[:, :, 1] = canvas[:, :, 1] * (1 - fw_f) + RIVER_COLOR[1] * fw_f
    canvas[:, :, 2] = canvas[:, :, 2] * (1 - fw_f) + RIVER_COLOR[2] * fw_f

    # ── Effet de rive (shoreline glow) ──────────────────────────────────────
    print("  Shoreline glow...")
    # Dilater le masque terre pour creer un anneau de rive
    land_img = PILImage.fromarray((land_mask.astype(np.uint8)) * 255)
    land_blurred = land_img.filter(ImageFilter.GaussianBlur(radius=8))
    shore_blend = np.array(land_blurred, dtype=np.float32) / 255.0
    # La rive = zone ou shore_blend est entre 0.1 et 0.9 (bord du masque)
    shore_zone = shore_blend * (1 - shore_blend) * 4  # max = 1 au milieu de la transition
    shore_zone = np.clip(shore_zone * 0.8, 0, 1)
    for c_idx, c_val in enumerate(SHORE_COLOR):
        canvas[:, :, c_idx] = canvas[:, :, c_idx] * (1 - shore_zone) + c_val * shore_zone

    # ── Flip vertical (Unity Y inversé) ──────────────────────────────────────
    canvas = canvas[::-1, :, :]

    # ── Convertir en uint8 et créer image PIL ────────────────────────────────
    canvas_u8 = np.clip(canvas, 0, 255).astype(np.uint8)
    img = PILImage.fromarray(canvas_u8, 'RGB')

    # ── Redimensionner si necessaire ─────────────────────────────────────────
    if out_size != t_side:
        img = img.resize((out_size, out_size), PILImage.LANCZOS)

    # ── Draw: routes et rivieres (PathData) ──────────────────────────────────
    print(f"  Dessin des {len(paths_raw)} chemins...")
    draw = ImageDraw.Draw(img)

    river_count = 0
    road_count = 0
    for path_bytes in paths_raw:
        name, nodes, width = parse_path_data(path_bytes, 0, len(path_bytes))

        if len(nodes) < 2:
            continue

        n_lower = name.lower()
        if n_lower.startswith('river'):
            color = RIVER_COLOR
            lw = max(3, int(width / map_size * out_size * 1.2))
            river_count += 1
        elif n_lower.startswith('rail'):
            color = RAIL_COLOR
            lw = max(1, int(width / map_size * out_size * 0.4))
            road_count += 1
        elif n_lower.startswith('powerline'):
            color = POWERLINE_COLOR
            lw = 1
            road_count += 1
        else:  # road
            color = ROAD_COLOR
            lw = max(2, int(width / map_size * out_size * 0.5))
            road_count += 1

        pts = []
        for wx, wz in nodes:
            px, py = world_to_pixel(wx, wz, map_size, out_size)
            pts.append((px, py))

        if len(pts) >= 2:
            draw.line(pts, fill=color, width=max(1, lw))

    print(f"  Rivieres: {river_count}, Routes: {road_count}")

    # ── Draw: monuments et structures (PrefabData) ────────────────────────────
    print(f"  Dessin des monuments ({len(prefabs_raw)} prefabs)...")
    monument_count = 0
    for pf_bytes in prefabs_raw:
        pid, category, px_w, pz_w = parse_prefab_data(pf_bytes, 0, len(pf_bytes))

        cat_lower = category.lower()
        cfg = None
        for key, val in MONUMENT_COLORS.items():
            if key in cat_lower:
                cfg = val
                break

        if cfg is None:
            continue  # Decor et autres non rendus

        fill_color, r = cfg
        outline_color = tuple(max(0, c - 50) for c in fill_color)

        px, py = world_to_pixel(px_w, pz_w, map_size, out_size)
        if 0 <= px < out_size and 0 <= py < out_size:
            draw.rectangle([px-r, py-r, px+r, py+r], fill=fill_color, outline=outline_color)
            monument_count += 1

    print(f"  {monument_count} monuments/structures dessines")

    # ── Sauvegarder ──────────────────────────────────────────────────────────
    img.save(output_path, 'PNG')
    fsize = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n  PNG sauvegarde: {output_path}")
    print(f"  Dimensions: {img.size[0]}x{img.size[1]}, Taille: {fsize:.1f} MB")
    return True


# ─── Point d'entree ───────────────────────────────────────────────────────────

def convert_rust_map(map_path, output_path=None, out_size=None):
    if output_path is None:
        output_path = os.path.splitext(map_path)[0] + '.png'

    print(f"\n{'='*60}")
    print(f"  {os.path.basename(map_path)}")
    print(f"{'='*60}\n")

    # Lire
    print("1. Lecture...")
    with open(map_path, 'rb') as f:
        raw = f.read()
    print(f"   {len(raw)/1024/1024:.1f} MB, version {struct.unpack('<I', raw[0:4])[0]}")

    # Decompresser
    print("\n2. Decompression LZ4...")
    proto_data = decompress_k4os_lz4_stream(raw[12:])
    if not proto_data:
        print("  ERREUR decompression"); return False

    # Parser
    print("\n3. Parsing WorldData...")
    map_size, maps, prefabs_raw, paths_raw = parse_world_data(proto_data)

    if not maps:
        print("  ERREUR: aucune couche"); return False

    # Rendre
    print("\n4. Rendu PNG...")
    render_map_png(map_size, maps, prefabs_raw, paths_raw, output_path, out_size=out_size)

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Convertit un fichier .map Rust en PNG',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'map_file',
        nargs='?',
        default=r'c:\Users\Djo\Desktop\maps rust covertion png\RedditMaps_4250_949694951_03-30-2026.map',
        help='Chemin vers le fichier .map (defaut: fichier RedditMaps)'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Chemin de sortie .png (defaut: meme nom que le .map)'
    )
    parser.add_argument(
        '-s', '--size',
        type=int,
        default=2048,
        help=(
            'Resolution de sortie en pixels (defaut: 2048)\n'
            'Exemples:\n'
            '  -s 1024   -> image 1024x1024\n'
            '  -s 2048   -> image 2048x2048\n'
            '  -s 4097   -> resolution native de la map\n'
            '  -s 4250   -> image 4250x4250\n'
            '  -s 0      -> resolution native automatique'
        )
    )

    args = parser.parse_args()

    # Taille 0 = resolution native
    out_size = args.size if args.size > 0 else None

    if out_size:
        print(f"Resolution de sortie: {out_size}x{out_size} pixels")
    else:
        print("Resolution de sortie: native (automatique)")

    success = convert_rust_map(args.map_file, args.output, out_size=out_size or 4097)

    if success:
        print("\nConversion reussie !")
    else:
        print("\nConversion echouee.")
        sys.exit(1)
