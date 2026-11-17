# model_services/test_data_generator.py
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "uploads" / "sample_data"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_changestar_sample_pair(
    output_dir: Path = SAMPLES_DIR,
    width: int = 512,
    height: int = 512
) -> tuple[Path, Path]:
    """
    Generates a realistic bi-temporal optical pair (T1 pre-change, T2 post-change):
    - T1: Agricultural / vegetative terrain with a road network.
    - T2: Same terrain plus newly constructed building clusters and cleared plots.
    """
    np.random.seed(42)

    # Base land cover (vegetation/soil texture)
    base_terrain = np.zeros((height, width, 3), dtype=np.uint8)
    base_terrain[:, :, 0] = np.random.randint(60, 95, size=(height, width))   # R (soil/shadows)
    base_terrain[:, :, 1] = np.random.randint(110, 155, size=(height, width)) # G (vegetation)
    base_terrain[:, :, 2] = np.random.randint(40, 75, size=(height, width))   # B

    img_t1 = Image.fromarray(base_terrain, mode="RGB")
    draw_t1 = ImageDraw.Draw(img_t1)

    # Draw primary road
    draw_t1.line([(0, height // 3), (width, height // 3 + 40)], fill=(130, 130, 130), width=16)
    draw_t1.line([(width // 2, 0), (width // 2 - 30, height)], fill=(120, 120, 120), width=12)

    # Existing pre-change structures
    draw_t1.rectangle([60, 60, 120, 120], fill=(180, 175, 160), outline=(90, 85, 75), width=2)
    draw_t1.rectangle([70, 140, 130, 190], fill=(160, 150, 140), outline=(80, 75, 70), width=2)

    # Copy T1 to T2 and introduce real changes (new building developments in T2)
    img_t2 = img_t1.copy()
    draw_t2 = ImageDraw.Draw(img_t2)

    # Cluster of new buildings (bright roofs typical of urban expansion)
    new_buildings = [
        (220, 220, 290, 280),
        (310, 230, 370, 285),
        (230, 305, 300, 360),
        (320, 310, 385, 365),
        (400, 180, 460, 240)
    ]
    for b in new_buildings:
        # Building roof (red/terracotta or concrete grey)
        draw_t2.rectangle(b, fill=(210, 80, 60), outline=(240, 240, 240), width=2)

    # Cleared construction ground
    draw_t2.rectangle([200, 200, 480, 390], outline=(170, 160, 130), width=1)

    t1_path = output_dir / "sample_t1_levir.png"
    t2_path = output_dir / "sample_t2_levir.png"

    img_t1.save(str(t1_path), format="PNG")
    img_t2.save(str(t2_path), format="PNG")
    return t1_path, t2_path


def generate_croma_sample_pair(
    output_dir: Path = SAMPLES_DIR,
    resolution: int = 120
) -> tuple[Path, Path]:
    """
    Generates paired Sentinel-1 SAR (2 channels) and Sentinel-2 Optical (12 channels)
    formatted specifically for CROMA Foundation Model inference.
    """
    np.random.seed(101)

    # 1. Sentinel-1 SAR: 2 channels (VV, VH backscatter in dB scale: typically -25 to 0 dB)
    sar_vv = np.random.normal(loc=-11.0, scale=3.5, size=(resolution, resolution)).astype(np.float32)
    sar_vh = np.random.normal(loc=-18.0, scale=4.0, size=(resolution, resolution)).astype(np.float32)

    # Inject double-bounce high backscatter feature (e.g. urban structures)
    sar_vv[40:70, 40:70] += 8.0
    sar_vh[40:70, 40:70] += 6.5

    sar_arr = np.stack([sar_vv, sar_vh], axis=0)  # [2, 120, 120]
    sar_path = output_dir / "sample_sentinel1_sar.npy"
    np.save(str(sar_path), sar_arr)

    # 2. Sentinel-2 Optical: 12 multispectral bands (surface reflectance 0 - 10000 scale)
    # Bands: B1(Coastal), B2(Blue), B3(Green), B4(Red), B5(VRE1), B6(VRE2), B7(VRE3), B8(NIR), B8A(NarrowNIR), B9(WaterVapor), B11(SWIR1), B12(SWIR2)
    optical_channels = []
    for band_idx in range(12):
        # Base reflectance varying across visible, red-edge, NIR, SWIR
        base_refl = 800.0 + (band_idx * 250.0)
        noise = np.random.normal(loc=base_refl, scale=120.0, size=(resolution, resolution))
        # Correlated feature matching the SAR structure
        noise[40:70, 40:70] += 1200.0
        optical_channels.append(noise.astype(np.float32))

    optical_arr = np.stack(optical_channels, axis=0)  # [12, 120, 120]
    optical_path = output_dir / "sample_sentinel2_optical.npy"
    np.save(str(optical_path), optical_arr)

    # Also save standard 3-channel RGB preview for visualization in frontend
    rgb_preview = np.stack([optical_arr[3], optical_arr[2], optical_arr[1]], axis=-1)
    rgb_preview = np.clip((rgb_preview / 3000.0) * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(rgb_preview).save(str(output_dir / "sample_sentinel2_rgb.png"))

    return sar_path, optical_path


if __name__ == "__main__":
    t1, t2 = generate_changestar_sample_pair()
    sar, opt = generate_croma_sample_pair()
    print(f"Generated ChangeStar pair: {t1}, {t2}")
    print(f"Generated CROMA pair: {sar}, {opt}")
