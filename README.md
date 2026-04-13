# 🗺️ Rust Map → PNG Converter

> Convert Rust game `.map` files into high-quality PNG images — with GUI, multilingual support, rivers, roads, monuments and realistic terrain rendering.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![Languages](https://img.shields.io/badge/Languages-6-orange)

---

## 📸 Preview

| Input | Output |
|-------|--------|
| `RedditMaps_4250_949694951.map` (47 MB) | `RedditMaps_4250_949694951.png` (2048×2048) |

<details>
<summary>Features visible in the output</summary>

- 🌊 Ocean with accurate teal color `#0B3A4A`
- ❄️ Snow zones, 🌿 Grasslands, 🏜️ Desert — from splat texture data
- 🏔️ Hillshading (directional light from the north-west)
- 🌊 Rivers & lakes (from water layer)
- 🛣️ Roads, 🚂 Rails, ⚡ Powerlines (from path data)
- 🏛️ Monuments, Dungeons and structures (from prefab data)
- 🌅 Shoreline glow effect at land/ocean boundary

</details>

---

## ✨ Features

- **Fully automatic** — just drop your `.map` file, get a PNG
- **Accurate rendering** — reads every data layer from the binary file
- **Multilingual GUI** — 🇫🇷 French · 🇬🇧 English · 🇪🇸 Spanish · 🇩🇪 German · 🇨🇳 Chinese · 🇷🇺 Russian
- **Custom resolution** — 1024 / 2048 / 4097 (native) / 4250 / any size
- **CLI + GUI** — use the graphical interface or the command line
- **Fast** — full conversion in ~10 seconds on a standard machine

---

## 🗂️ File Structure

```
├── rust_map_to_png.py   # Core converter (CLI)
├── rust_map_gui.py      # Graphical interface (tkinter)
├── README.md
└── requirements.txt
```

---

## ⚙️ How it works

Rust `.map` files use a custom binary format:

```
[4 bytes]  World Serialization version (currently 10)
[8 bytes]  Timestamp
[rest]     K4os.Compression.LZ4.Legacy stream
              └─ Protobuf WorldData
                    ├─ uint32  size          (map size in meters)
                    ├─ MapData terrain       (4097×4097 uint16 heightmap)
                    ├─ MapData water         (4097×4097 uint16 water height)
                    ├─ MapData splat         (2048×2048 × 8 ground type weights)
                    ├─ MapData biome         (2048×2048 × 5 biome weights)
                    ├─ MapData topology      (2048×2048 int32 flags per pixel)
                    ├─ MapData alpha         (2048×2048 terrain mask)
                    ├─ PrefabData × 35 000+  (monuments, decor, roads objects)
                    └─ PathData  × 131       (roads, rivers, rails, powerlines)
```

The converter:
1. Decodes the **K4os LZ4 Legacy** chunk stream (variable-length VarInt headers)
2. Parses the **Protobuf WorldData** manually (no .proto file needed)
3. Renders terrain using **splat layer** (8 ground types blended by weight)
4. Detects **ocean** from `topology` flag `Lake` (bit 7)
5. Applies **hillshading** (Lambertian directional light)
6. Draws **rivers**, **roads**, **rails**, **powerlines** from `PathData` nodes
7. Places **monument** markers from `PrefabData` (category `Monument` / `Dungeon`)

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- pip

### Install dependencies

```bash
pip install lz4 Pillow numpy
```

---

## 🖥️ Usage

### Graphical Interface (recommended)

```bash
python rust_map_gui.py
```

![GUI screenshot placeholder](docs/gui_preview.png)

1. Click **Browse** to select your `.map` file
2. Choose an output folder
3. Pick a resolution (1024 / 2048 / 4097 / 4250 / custom)
4. Click **Convert**
5. Open the PNG directly from the interface

> **Switch language** at any time using the dropdown in the top-right corner (🇫🇷 🇬🇧 🇪🇸 🇩🇪 🇨🇳 🇷🇺)

---

### Command Line

```bash
# Default (2048×2048)
python rust_map_to_png.py MyMap.map

# Custom resolution
python rust_map_to_png.py MyMap.map -s 4250

# Specify output path
python rust_map_to_png.py MyMap.map -s 2048 -o output/map.png

# Native resolution (4097×4097)
python rust_map_to_png.py MyMap.map -s 0

# Help
python rust_map_to_png.py --help
```

#### All CLI options

| Option | Description | Default |
|--------|-------------|---------|
| `map_file` | Path to the `.map` file | — |
| `-o`, `--output` | Output `.png` path | same name as input |
| `-s`, `--size` | Output resolution in pixels | `2048` |

---

## 🎨 Rendered Layers

| Layer | Source | Description |
|-------|--------|-------------|
| **Terrain color** | `splat` | 8 ground types (Dirt, Snow, Sand, Rock, Grass, Forest, Stones, Gravel) blended by weight |
| **Hillshading** | `terrain` | Directional light from NW at 45° |
| **Ocean** | `topology` (Lake bit) | Dark teal `#0B3A4A` |
| **Shoreline** | Edge of ocean mask | Soft white glow |
| **Rivers / Lakes** | `water` | Blue `#195A8C` |
| **Roads** | `PathData` | Dark `#282623` lines |
| **Rails** | `PathData` | Gray lines |
| **Powerlines** | `PathData` | Olive lines |
| **Monuments** | `PrefabData` | Orange `#B4823C` squares |
| **Dungeons** | `PrefabData` | Brown squares |

---

## 🗺️ Supported Map Formats

| Version | Supported |
|---------|-----------|
| v9 (older servers) | ✅ |
| v10 (current Facepunch) | ✅ |
| Custom maps (RustEdit) | ✅ |
| Procedural maps | ✅ |
| Barren maps | ✅ |

---

## 📋 Requirements

```
lz4>=4.0.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## 📄 License

MIT License — free to use, modify and distribute.

---

## 🙏 Credits

- [Facepunch Studios](https://facepunch.com/) — Rust game & map format documentation
- [Rust Map Making Wiki](https://wiki.rustmapmaking.com/) — Community format research
- [K4os.Compression.LZ4](https://github.com/MiloszKrajewski/K4os.Compression.LZ4) — LZ4 Legacy stream format

---

## 🤝 Contributing

Pull requests are welcome! Areas for improvement:
- [ ] Better monument icons (by prefab ID)
- [ ] Add grid/coordinates overlay
- [ ] Barren map biome support
- [ ] Export as interactive HTML (Leaflet)
- [ ] Mac/Linux support for the GUI launcher
