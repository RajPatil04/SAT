"""
Procedural generator for SatQuery AI realistic satellite imagery,
evidence layers, and visual background assets.
"""
import os
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "samples")
STATIC_ASSETS_DIR = os.path.join(BASE_DIR, "ui", "static", "assets")

def ensure_dirs():
    for sub in ["single_image", "bi_temporal", "optical_sar"]:
        os.makedirs(os.path.join(DATA_DIR, sub), exist_ok=True)
    os.makedirs(STATIC_ASSETS_DIR, exist_ok=True)

def create_river_mask(width=640, height=640):
    """Creates a winding river path mask."""
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    points = []
    num_pts = 30
    for i in range(num_pts):
        y = int(i * (height / (num_pts - 1)))
        # S-curves
        x = int(width * 0.45 + width * 0.25 * math.sin(i * 0.35) + width * 0.1 * math.cos(i * 0.7))
        points.append((x, y))
        
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=255, width=42)
    
    # Add a tributary
    trib_points = []
    for i in range(15):
        y = int(height * 0.35 + i * (height * 0.45 / 14))
        x = int(width * 0.15 + i * (width * 0.35 / 14) + math.sin(i * 0.5) * 15)
        trib_points.append((x, y))
    for i in range(len(trib_points) - 1):
        draw.line([trib_points[i], trib_points[i+1]], fill=255, width=20)

    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))
    return mask

def generate_single_image_dataset():
    """Generates optical satellite image + 4 evidence layers matching the reference screenshot."""
    w, h = 640, 640
    single_dir = os.path.join(DATA_DIR, "single_image")
    
    # Base terrain: agricultural patchwork + vegetation
    np.random.seed(42)
    
    # Field grid pattern
    grid_size = 32
    field_colors = [
        (34, 76, 38),    # Deep forest green
        (46, 110, 52),   # Lush pasture
        (65, 128, 60),   # Light crop
        (85, 135, 75),   # Golden-green field
        (120, 115, 65),  # Dry agriculture / fallow
        (40, 85, 45),    # Dense canopy
        (130, 100, 70),  # Tilled soil
    ]
    
    base_img = Image.new("RGB", (w, h), (40, 80, 45))
    draw = ImageDraw.Draw(base_img)
    
    # Draw patchwork fields
    for gx in range(0, w, grid_size):
        for gy in range(0, h, grid_size):
            jitter_x = int(np.random.uniform(-4, 4))
            jitter_y = int(np.random.uniform(-4, 4))
            c = field_colors[np.random.randint(0, len(field_colors))]
            draw.rectangle([gx, gy, gx + grid_size + jitter_x, gy + grid_size + jitter_y], fill=c)
            
    # Add urban / built-up clusters in specific zones (middle-right and lower right)
    for bx in range(360, 580, 12):
        for by in range(240, 520, 12):
            if np.random.rand() > 0.3:
                val = int(np.random.uniform(140, 200))
                draw.rectangle([bx, by, bx + 8, by + 8], fill=(val, val - 10, val - 20))
                
    # Add roads
    road_draw = ImageDraw.Draw(base_img)
    for _ in range(8):
        y_r = int(np.random.uniform(50, h - 50))
        road_draw.line([(0, y_r), (w, y_r + int(np.random.uniform(-80, 80)))], fill=(160, 160, 165), width=3)
    for _ in range(6):
        x_r = int(np.random.uniform(50, w - 50))
        road_draw.line([(x_r, 0), (x_r + int(np.random.uniform(-60, 60)), h)], fill=(150, 150, 155), width=3)

    # Texture & grain
    base_arr = np.array(base_img).astype(np.float32)
    noise = np.random.normal(0, 8, base_arr.shape)
    base_arr = np.clip(base_arr + noise, 0, 255).astype(np.uint8)
    base_img = Image.fromarray(base_arr)

    # Composite river (water body)
    river_mask = create_river_mask(w, h)
    river_arr = np.array(river_mask) / 255.0
    
    # Water color: deep blue-green / dark teal
    img_arr = np.array(base_img).astype(np.float32)
    water_color = np.array([12, 45, 62], dtype=np.float32)
    
    for c in range(3):
        img_arr[:, :, c] = img_arr[:, :, c] * (1.0 - river_arr) + water_color[c] * river_arr
    
    optical_img = Image.fromarray(np.clip(img_arr, 0, 255).astype(np.uint8))
    optical_img.save(os.path.join(single_dir, "image.png"))
    
    # 1. Evidence Thumbnail 1: Zoom / River detail
    zoom_img = optical_img.crop((180, 180, 460, 460)).resize((w, h), Image.Resampling.LANCZOS)
    zoom_img.save(os.path.join(single_dir, "zoom.png"))

    # 2. Evidence Thumbnail 2: Land Cover Segmentation Mask (Color coded according to legend)
    # Legend: Vegetation (green #22c55e), Water Body (#3b82f6), Built-up (#ef4444), Agriculture (#eab308), Roads (#cbd5e1)
    seg_arr = np.zeros((w, h, 3), dtype=np.uint8)
    # Default: vegetation
    seg_arr[:, :] = [34, 197, 94]
    
    # Agriculture regions
    for gx in range(0, w, grid_size * 2):
        for gy in range(0, h, grid_size * 2):
            if (gx + gy) % 3 == 0:
                seg_arr[gy:gy+grid_size*2, gx:gx+grid_size*2] = [234, 179, 8] # Agriculture
                
    # Urban areas
    seg_arr[240:520, 360:580] = [239, 68, 68] # Built-up
    
    # River in mask: blue
    for c, val in enumerate([59, 130, 246]):
        seg_arr[:, :, c] = (seg_arr[:, :, c] * (1.0 - river_arr) + val * river_arr).astype(np.uint8)

    seg_img = Image.fromarray(seg_arr).filter(ImageFilter.GaussianBlur(radius=1.5))
    seg_img.save(os.path.join(single_dir, "segmentation.png"))

    # 3. Evidence Thumbnail 3: Grayscale / SAR / Texture representation
    gray_arr = np.array(optical_img.convert("L")).astype(np.float32)
    speckle = np.random.gamma(4, 0.25, gray_arr.shape)
    sar_like = np.clip(gray_arr * speckle, 0, 255).astype(np.uint8)
    sar_img = Image.fromarray(sar_like)
    sar_img.save(os.path.join(single_dir, "sar_feature.png"))

    # 4. Evidence Thumbnail 4: False-Color Infrared / NDVI
    ndvi_arr = np.zeros((w, h, 3), dtype=np.uint8)
    ndvi_arr[:, :, 0] = np.clip(base_arr[:, :, 1] * 1.3 + 30, 0, 255)
    ndvi_arr[:, :, 1] = np.clip(base_arr[:, :, 0] * 0.4, 0, 255)
    ndvi_arr[:, :, 2] = np.clip(base_arr[:, :, 2] * 1.6 + 60, 0, 255)
    for c in range(3):
        ndvi_arr[:, :, c] = (ndvi_arr[:, :, c] * (1.0 - river_arr)).astype(np.uint8)
    ndvi_img = Image.fromarray(ndvi_arr).filter(ImageFilter.GaussianBlur(radius=1))
    ndvi_img.save(os.path.join(single_dir, "ndvi.png"))

    # result.json
    result_data = {
        "task": "Single-image Understanding",
        "model": "GeoChat",
        "input_type": "1 image (optical)",
        "modality": "Optical",
        "acquisition_date": "2024-05-15",
        "filename": "test_image.tif",
        "format": "GeoTIFF",
        "dimensions": "1024 × 1024",
        "bands": "4 (RGB + NIR)",
        "status": "Analysis Ready",
        "answer": "The image shows a mix of agricultural fields, a river, and urban built-up areas. The dominant land cover is vegetation with clear signs of human settlement near the riverbanks.",
        "confidence": 0.92,
        "confidence_level": "High Confidence",
        "detected_land_cover": [
            {"label": "Vegetation", "color": "#22c55e", "percentage": 52},
            {"label": "Water Body", "color": "#3b82f6", "percentage": 14},
            {"label": "Built-up Area", "color": "#ef4444", "percentage": 18},
            {"label": "Agriculture", "color": "#eab308", "percentage": 12},
            {"label": "Roads", "color": "#cbd5e1", "percentage": 4}
        ],
        "evidence": [
            {"id": "main", "label": "Input Image", "file": "image.png", "type": "RGB Optical"},
            {"id": "seg", "label": "Land Cover Segmentation", "file": "segmentation.png", "type": "Multi-class Mask"},
            {"id": "sar", "label": "SAR Backscatter", "file": "sar_feature.png", "type": "Radar Feature"},
            {"id": "ndvi", "label": "NIR False Color", "file": "ndvi.png", "type": "Multispectral Index"}
        ],
        "execution_trace": [
            {"step": "01", "name": "Input Validation", "desc": "Checked format, metadata, compatibility", "status": "Completed"},
            {"step": "02", "name": "Query Understanding", "desc": "Identified as single-image analysis", "status": "Completed"},
            {"step": "03", "name": "Agent Routing", "desc": "Selected GeoChat model", "status": "Completed"},
            {"step": "04", "name": "Model Execution", "desc": "VQA + Captioning", "status": "Completed"},
            {"step": "05", "name": "Result Integration", "desc": "Combined output with spatial evidence", "status": "Completed"},
            {"step": "06", "name": "Final Output", "desc": "Answer + Visual evidence + Confidence", "status": "Completed"}
        ]
    }
    
    with open(os.path.join(single_dir, "result.json"), "w") as f:
        json.dump(result_data, f, indent=2)
    print("Generated single_image dataset.")

def generate_bi_temporal_dataset():
    """Generates 2024 Before, 2026 After, and Change Detection Map."""
    w, h = 640, 640
    bi_dir = os.path.join(DATA_DIR, "bi_temporal")
    np.random.seed(101)
    
    before_img = Image.new("RGB", (w, h), (45, 95, 50))
    draw_before = ImageDraw.Draw(before_img)
    
    for x in range(0, w, 28):
        for y in range(0, h, 28):
            val_g = int(np.random.uniform(70, 130))
            draw_before.rectangle([x, y, x+26, y+26], fill=(30, val_g, 40))
            
    draw_before.rectangle([200, 200, 280, 280], fill=(130, 125, 120))
    river_mask = create_river_mask(w, h)
    r_arr = np.array(river_mask) / 255.0
    
    b_arr = np.array(before_img).astype(np.float32)
    for c, val in enumerate([14, 52, 75]):
        b_arr[:, :, c] = b_arr[:, :, c] * (1.0 - r_arr) + val * r_arr
    before_img = Image.fromarray(np.clip(b_arr, 0, 255).astype(np.uint8))
    before_img.save(os.path.join(bi_dir, "before.png"))

    after_img = before_img.copy()
    draw_after = ImageDraw.Draw(after_img)
    
    draw_after.rectangle([180, 180, 420, 380], fill=(165, 155, 145))
    for bx in range(200, 400, 24):
        for by in range(200, 360, 20):
            draw_after.rectangle([bx, by, bx+18, by+14], fill=(195, 200, 210))
            
    draw_after.line([(50, 480), (590, 280)], fill=(185, 185, 190), width=6)
    draw_after.line([(300, 180), (300, 520)], fill=(175, 175, 180), width=4)
    draw_after.line([(180, 280), (450, 280)], fill=(175, 175, 180), width=4)
    after_img.save(os.path.join(bi_dir, "after.png"))

    change_arr = np.zeros((w, h, 3), dtype=np.uint8)
    change_arr[:, :] = [12, 18, 30]
    
    change_mask = Image.new("L", (w, h), 0)
    c_draw = ImageDraw.Draw(change_mask)
    c_draw.rectangle([180, 180, 420, 380], fill=255)
    c_draw.line([(50, 480), (590, 280)], fill=255, width=12)
    change_mask = change_mask.filter(ImageFilter.GaussianBlur(radius=4))
    
    cm_arr = np.array(change_mask) / 255.0
    for c, val in enumerate([249, 115, 22]):
        change_arr[:, :, c] = (change_arr[:, :, c] * (1.0 - cm_arr) + val * cm_arr).astype(np.uint8)
        
    change_img = Image.fromarray(change_arr)
    change_img.save(os.path.join(bi_dir, "change_map.png"))

    result_data = {
        "task": "Bi-temporal Change Analysis",
        "model": "ChangeStar",
        "input_type": "2 images (optical pair: 2024 vs 2026)",
        "modality": "Bi-temporal Optical",
        "acquisition_date": "2024-04-12 / 2026-03-08",
        "filename": "pair_2024_2026.tif",
        "format": "GeoTIFF Pair",
        "dimensions": "1024 × 1024",
        "bands": "4 Bands per epoch",
        "status": "Analysis Ready",
        "answer": "Significant urban expansion and new infrastructure development detected. Built-up area increased by approximately +38.4 hectares between 2024 and 2026, primarily replacing former pasture and forest land with a new transportation corridor.",
        "confidence": 0.89,
        "confidence_level": "High Confidence",
        "detected_land_cover": [
            {"label": "New Built-up Area", "color": "#f97316", "percentage": 24},
            {"label": "Intact Vegetation", "color": "#22c55e", "percentage": 48},
            {"label": "Water Body (Unchanged)", "color": "#3b82f6", "percentage": 14},
            {"label": "Cleared Land", "color": "#eab308", "percentage": 9},
            {"label": "New Highway Corridor", "color": "#cbd5e1", "percentage": 5}
        ],
        "evidence": [
            {"id": "before", "label": "2024 Before Image", "file": "before.png", "type": "Historical Baseline"},
            {"id": "after", "label": "2026 After Image", "file": "after.png", "type": "Current Observation"},
            {"id": "change", "label": "Change Detection Map", "file": "change_map.png", "type": "ChangeStar Delta Map"}
        ],
        "execution_trace": [
            {"step": "01", "name": "Input Validation", "desc": "Validated dual epoch GeoTIFFs & spatial co-registration", "status": "Completed"},
            {"step": "02", "name": "Query Understanding", "desc": "Identified task as bi-temporal delta detection", "status": "Completed"},
            {"step": "03", "name": "Agent Routing", "desc": "Routed to ChangeStar specialist", "status": "Completed"},
            {"step": "04", "name": "Model Execution", "desc": "Dense temporal cross-attention & segmentation", "status": "Completed"},
            {"step": "05", "name": "Result Integration", "desc": "Computed change polygon statistics & delta mask", "status": "Completed"},
            {"step": "06", "name": "Final Output", "desc": "Delivered change map and quantitative impact report", "status": "Completed"}
        ]
    }
    with open(os.path.join(bi_dir, "result.json"), "w") as f:
        json.dump(result_data, f, indent=2)
    print("Generated bi_temporal dataset.")

def generate_optical_sar_dataset():
    """Generates Optical + SAR + CROMA Joint Fusion."""
    w, h = 640, 640
    opt_sar_dir = os.path.join(DATA_DIR, "optical_sar")
    np.random.seed(202)
    
    opt_img = Image.new("RGB", (w, h), (40, 90, 48))
    draw_opt = ImageDraw.Draw(opt_img)
    
    for x in range(0, w, 32):
        for y in range(0, h, 32):
            draw_opt.rectangle([x, y, x+30, y+30], fill=(int(np.random.uniform(30, 80)), int(np.random.uniform(80, 140)), int(np.random.uniform(35, 70))))
            
    river_mask = create_river_mask(w, h)
    r_arr = np.array(river_mask) / 255.0
    opt_arr = np.array(opt_img).astype(np.float32)
    for c, val in enumerate([15, 60, 90]):
        opt_arr[:, :, c] = opt_arr[:, :, c] * (1.0 - r_arr) + val * r_arr
        
    cloud_mask = Image.new("L", (w, h), 0)
    c_draw = ImageDraw.Draw(cloud_mask)
    c_draw.ellipse([30, 30, 240, 180], fill=220)
    cloud_mask = cloud_mask.filter(ImageFilter.GaussianBlur(radius=20))
    cl_arr = np.array(cloud_mask) / 255.0
    
    for c in range(3):
        opt_arr[:, :, c] = opt_arr[:, :, c] * (1.0 - cl_arr * 0.85) + 245 * (cl_arr * 0.85)
        
    opt_final = Image.fromarray(np.clip(opt_arr, 0, 255).astype(np.uint8))
    opt_final.save(os.path.join(opt_sar_dir, "optical.png"))

    sar_arr = np.zeros((w, h), dtype=np.float32)
    veg_speckle = np.random.gamma(3.0, 30.0, (w, h))
    sar_arr += veg_speckle
    sar_arr[260:500, 340:560] += np.random.uniform(150, 240, (240, 220))
    sar_arr[60:160, 70:200] += np.random.uniform(160, 250, (100, 130))
    sar_arr = sar_arr * (1.0 - r_arr * 0.95) + 12.0 * r_arr
    
    sar_final = Image.fromarray(np.clip(sar_arr, 0, 255).astype(np.uint8))
    sar_final.save(os.path.join(opt_sar_dir, "sar.png"))

    fusion_arr = np.zeros((w, h, 3), dtype=np.uint8)
    fusion_arr[:, :, 0] = np.clip(np.array(sar_final) * 0.8 + 20, 0, 255)
    fusion_arr[:, :, 1] = np.clip(np.array(opt_final.convert("L")) * 0.6, 0, 255)
    fusion_arr[:, :, 2] = np.clip(np.array(opt_final.convert("L")) * 0.9 + 50, 0, 255)
    
    for c, val in enumerate([10, 24, 48]):
        fusion_arr[:, :, c] = (fusion_arr[:, :, c] * (1.0 - r_arr) + val * r_arr).astype(np.uint8)
        
    fusion_img = Image.fromarray(fusion_arr).filter(ImageFilter.GaussianBlur(radius=1))
    fusion_img.save(os.path.join(opt_sar_dir, "joint_analysis.png"))

    result_data = {
        "task": "Cross-modal Analysis",
        "model": "CROMA",
        "input_type": "2 images (Optical + SAR Sentinel Pair)",
        "modality": "Optical + SAR Cross-Modal",
        "acquisition_date": "2025-11-20",
        "filename": "s2_s1_colocated.tif",
        "format": "Multispectral + C-Band SAR",
        "dimensions": "1024 × 1024",
        "bands": "Optical (B2,B3,B4,B8) + SAR (VV, VH)",
        "status": "Analysis Ready",
        "answer": "Cross-modal fusion successfully disambiguated cloud-obscured surface features in the north-west sector. SAR backscatter identified hidden industrial structures beneath cloud cover while optical spectral bands accurately delineated agricultural plots and river boundary geometry.",
        "confidence": 0.94,
        "confidence_level": "High Confidence",
        "detected_land_cover": [
            {"label": "Cloud-Penetrated Structures", "color": "#a855f7", "percentage": 16},
            {"label": "Vegetation / Agriculture", "color": "#22c55e", "percentage": 50},
            {"label": "Water Body (Specular)", "color": "#3b82f6", "percentage": 14},
            {"label": "Urban Settlement", "color": "#ef4444", "percentage": 15},
            {"label": "Transport Arteries", "color": "#cbd5e1", "percentage": 5}
        ],
        "evidence": [
            {"id": "optical", "label": "Optical S2 Imagery", "file": "optical.png", "type": "Multispectral Optical"},
            {"id": "sar", "label": "SAR S1 Radar Backscatter", "file": "sar.png", "type": "C-band Co-pol Radar"},
            {"id": "joint", "label": "CROMA Joint Analysis", "file": "joint_analysis.png", "type": "Cross-Modal Representation"}
        ],
        "execution_trace": [
            {"step": "01", "name": "Input Validation", "desc": "Validated Optical (S2) and SAR (S1) spatial alignment", "status": "Completed"},
            {"step": "02", "name": "Query Understanding", "desc": "Identified cross-modal fusion & feature disambiguation", "status": "Completed"},
            {"step": "03", "name": "Agent Routing", "desc": "Selected CROMA multimodal specialist", "status": "Completed"},
            {"step": "04", "name": "Model Execution", "desc": "Cross-attention optical-radar encoder fusion", "status": "Completed"},
            {"step": "05", "name": "Result Integration", "desc": "Merged cloud-penetrated structures with optical mask", "status": "Completed"},
            {"step": "06", "name": "Final Output", "desc": "Delivered joint cross-modal synthesis & classification", "status": "Completed"}
        ]
    }
    with open(os.path.join(opt_sar_dir, "result.json"), "w") as f:
        json.dump(result_data, f, indent=2)
    print("Generated optical_sar dataset.")

def generate_background_assets():
    """Generates realistic Earth horizon and satellite illustration assets for the header and cards."""
    bw, bh = 1920, 260
    header_bg = Image.new("RGBA", (bw, bh), (7, 11, 20, 255))
    draw = ImageDraw.Draw(header_bg)
    
    np.random.seed(99)
    for _ in range(150):
        sx = int(np.random.uniform(0, bw))
        sy = int(np.random.uniform(0, bh * 0.7))
        star_alpha = int(np.random.uniform(40, 200))
        star_size = 1 if np.random.rand() > 0.1 else 2
        draw.rectangle([sx, sy, sx + star_size, sy + star_size], fill=(210, 230, 255, star_alpha))
        
    cx, cy = bw * 0.58, bh * 3.7
    r = bh * 3.45
    
    for glow_offset, alpha in [(40, 15), (28, 25), (18, 45), (10, 85), (3, 150)]:
        draw.ellipse([cx - (r + glow_offset), cy - (r + glow_offset), cx + (r + glow_offset), cy + (r + glow_offset)], 
                     outline=(56, 189, 248, alpha), width=3)
        
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(12, 32, 65, 245), outline=(96, 165, 250, 220), width=2)
    
    header_bg = header_bg.filter(ImageFilter.GaussianBlur(radius=0.5))
    header_bg.save(os.path.join(STATIC_ASSETS_DIR, "header_earth_bg.png"))
    print("Generated header_earth_bg.png.")

if __name__ == "__main__":
    ensure_dirs()
    generate_single_image_dataset()
    generate_bi_temporal_dataset()
    generate_optical_sar_dataset()
    generate_background_assets()
    print("All assets generated successfully!")
