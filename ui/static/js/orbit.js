/**
 * SatQuery AI - Ultra-Realistic 3D Earth & Satellite Orbital Simulation
 * Features:
 * - Real continental landmass projections (Africa, Americas, Eurasia, Australia, Ice Caps)
 * - Deep multi-tone oceans with specular sunlight glint
 * - Rayleigh atmospheric limb scattering and ethereal blue aura
 * - Two-layer dynamic cloud parallax with realistic atmospheric swirl
 * - Night-side illuminated city lights (twinkling urban centers)
 * - High-detail 3D Satellite model: gold foil thermal MLI body, solar panel arrays, antenna
 * - Active radar/optical scanning beam projecting from satellite to Earth surface
 * - High-DPI crisp rendering supporting retina displays
 */

// Comprehensive real-world continent landmass coordinates [latitude, longitude]
const EARTH_CONTINENTS = [
  // North America
  [
    [71, -156], [70, -135], [68, -100], [60, -65], [47, -53], [44, -64], [35, -75],
    [25, -80], [30, -85], [29, -95], [25, -97], [18, -95], [15, -89], [8, -77],
    [9, -84], [16, -93], [20, -105], [32, -117], [38, -123], [48, -125], [55, -132],
    [60, -140], [60, -150], [55, -165], [65, -168], [71, -156]
  ],
  // South America
  [
    [12, -72], [10, -62], [7, -53], [-3, -40], [-8, -35], [-20, -40], [-23, -43],
    [-35, -53], [-45, -65], [-55, -68], [-53, -73], [-40, -73], [-30, -71], [-18, -70],
    [-5, -81], [2, -77], [12, -72]
  ],
  // Eurasia (Europe + Asia)
  [
    [36, -5], [43, -9], [48, -4], [50, 1], [58, -5], [58, 7], [54, 18], [60, 28],
    [70, 28], [71, 52], [69, 68], [73, 80], [77, 105], [74, 135], [70, 160], [66, 170],
    [60, 165], [60, 150], [53, 142], [43, 132], [38, 120], [30, 122], [22, 114],
    [22, 108], [10, 107], [1, 104], [15, 96], [22, 90], [22, 80], [8, 77], [20, 72],
    [25, 68], [25, 57], [12, 44], [30, 32], [32, 25], [37, 22], [36, 10], [42, 3], [36, -5]
  ],
  // Africa
  [
    [37, 10], [32, 25], [30, 32], [22, 37], [12, 44], [11, 51], [2, 45], [-5, 40],
    [-10, 40], [-15, 35], [-25, 32], [-34, 26], [-34, 18], [-28, 16], [-22, 14],
    [-12, 13], [-5, 12], [4, 9], [5, 2], [6, -2], [4, -7], [6, -10], [10, -14],
    [15, -17], [21, -17], [28, -13], [32, -8], [36, -5], [37, 2], [37, 10]
  ],
  // Australia
  [
    [-12, 132], [-14, 136], [-12, 142], [-23, 150], [-32, 153], [-38, 147], [-38, 140],
    [-35, 136], [-32, 132], [-35, 118], [-32, 115], [-22, 114], [-17, 122], [-14, 126], [-12, 132]
  ],
  // Greenland
  [
    [77, -20], [82, -30], [83, -40], [78, -68], [70, -55], [60, -44], [65, -38], [70, -25], [77, -20]
  ],
  // Antarctica
  [
    [-65, -60], [-70, 0], [-66, 60], [-66, 120], [-70, 160], [-75, 180], [-80, -150], [-72, -90], [-65, -60]
  ],
  // Major Islands (UK, Madagascar, Japan)
  [
    [58, -3], [56, -6], [50, -5], [51, 1], [55, 0], [58, -3]
  ],
  [
    [-12, 49], [-16, 49], [-25, 47], [-25, 44], [-16, 44], [-12, 49]
  ],
  [
    [45, 142], [40, 140], [35, 136], [32, 130], [35, 133], [40, 142], [45, 142]
  ]
];

// Major city lights on night side [lat, lon, size, intensity]
const NIGHT_CITIES = [
  [40.7, -74.0, 1.8, 0.9],   // New York
  [34.0, -118.2, 1.6, 0.85], // Los Angeles
  [41.8, -87.6, 1.4, 0.8],   // Chicago
  [51.5, -0.1, 1.8, 0.9],    // London
  [48.8, 2.35, 1.6, 0.85],   // Paris
  [55.7, 37.6, 1.5, 0.8],    // Moscow
  [35.7, 139.7, 2.0, 0.95],  // Tokyo
  [31.2, 121.5, 1.8, 0.9],   // Shanghai
  [28.6, 77.2, 1.9, 0.9],    // Delhi
  [19.0, 72.8, 1.7, 0.85],   // Mumbai
  [1.35, 103.8, 1.5, 0.8],   // Singapore
  [-23.5, -46.6, 1.6, 0.85], // Sao Paulo
  [-34.6, -58.4, 1.4, 0.75], // Buenos Aires
  [30.0, 31.2, 1.5, 0.8],    // Cairo
  [-26.2, 28.0, 1.4, 0.75],  // Johannesburg
  [-33.8, 151.2, 1.5, 0.8]   // Sydney
];

// Procedural swirling atmospheric cloud bands [lat, lon, sizeX, sizeY]
const CLOUD_SWIRLS = [
  [55, -40, 32, 14],
  [45, 20, 28, 12],
  [12, -25, 42, 10],
  [-10, 60, 35, 12],
  [-48, 110, 48, 16],
  [35, 145, 30, 14],
  [-20, -75, 36, 12],
  [65, 80, 40, 15],
  [-55, -120, 45, 18],
  [22, -150, 25, 10]
];

/**
 * Initializes realistic 3D Earth simulation on given canvas
 */
function initRealisticEarthCanvas(canvasId, options = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const isMini = options.isMini || false;
  const dpr = window.devicePixelRatio || 2;

  // Sizing with high-DPI scaling
  const cssWidth = options.width || (canvas.parentElement ? canvas.parentElement.clientWidth : 140) || 140;
  const cssHeight = options.height || 140;

  canvas.width = cssWidth * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;

  ctx.scale(dpr, dpr);

  const cx = cssWidth / 2;
  const cy = cssHeight / 2;
  const earthRadius = isMini ? 18 : 38;

  // Animation states
  let earthAngle = 0;
  let cloudAngle = 0;
  let satAngle1 = 0;
  let satAngle2 = Math.PI * 0.75;
  let scanPulse = 0;

  // Normalized Sun Light Direction Vector (Sun coming from top-left front)
  const sunDir = [-0.55, -0.45, 0.7];
  const sunLen = Math.hypot(...sunDir);
  const Lx = sunDir[0] / sunLen;
  const Ly = sunDir[1] / sunLen;
  const Lz = sunDir[2] / sunLen;

  function renderFrame() {
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    // -------------------------------------------------------------
    // 1. OUTER ATMOSPHERIC RAYLEIGH SCATTERING GLOW (Halo)
    // -------------------------------------------------------------
    const auraRadius = earthRadius * (isMini ? 1.45 : 1.55);
    const atmoGlow = ctx.createRadialGradient(cx, cy, earthRadius * 0.85, cx, cy, auraRadius);
    atmoGlow.addColorStop(0, "rgba(56, 189, 248, 0.48)");
    atmoGlow.addColorStop(0.3, "rgba(37, 99, 235, 0.28)");
    atmoGlow.addColorStop(0.7, "rgba(14, 165, 233, 0.1)");
    atmoGlow.addColorStop(1, "rgba(2, 6, 23, 0)");

    ctx.fillStyle = atmoGlow;
    ctx.beginPath();
    ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2);
    ctx.fill();

    // -------------------------------------------------------------
    // 2. ORBIT TRACKS (Back Half - Behind Earth)
    // -------------------------------------------------------------
    if (!isMini) {
      drawOrbitTrack(ctx, cx, cy, earthRadius * 1.48, earthRadius * 0.65, -0.4, true);
      drawOrbitTrack(ctx, cx, cy, earthRadius * 1.58, earthRadius * 0.52, 0.62, true);
    }

    // -------------------------------------------------------------
    // 3. 3D EARTH GLOBE SPHERE (Clipped to Circle)
    // -------------------------------------------------------------
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, earthRadius, 0, Math.PI * 2);
    ctx.clip();

    // 3A. DEEP OCEAN BASE GRADIENT (Sapphire / Navy with Specular Light)
    const oceanGrad = ctx.createRadialGradient(
      cx - earthRadius * 0.4,
      cy - earthRadius * 0.4,
      earthRadius * 0.08,
      cx,
      cy,
      earthRadius
    );
    oceanGrad.addColorStop(0, "#1e40af"); // Sunlight reflected on water
    oceanGrad.addColorStop(0.25, "#1d4ed8");
    oceanGrad.addColorStop(0.55, "#0f2b5c");
    oceanGrad.addColorStop(0.85, "#081b3a");
    oceanGrad.addColorStop(1, "#020b18"); // Deep dark ocean abyss

    ctx.fillStyle = oceanGrad;
    ctx.fillRect(cx - earthRadius, cy - earthRadius, earthRadius * 2, earthRadius * 2);

    // 3B. CONTINENTAL LANDMASSES (Projected 3D Spherical Polygons)
    drawContinents(ctx, cx, cy, earthRadius, earthAngle);

    // 3C. NIGHT-SIDE TWINKLING CITY LIGHTS
    drawCityLights(ctx, cx, cy, earthRadius, earthAngle, Lx, Ly, Lz, isMini);

    // 3D. DYNAMIC SWIRLING CLOUD LAYER (Rotates at separate speed for parallax)
    drawCloudLayer(ctx, cx, cy, earthRadius, cloudAngle, isMini);

    // 3E. 3D SPHERE SHADING & DAY/NIGHT TERMINATOR
    // Smooth shadow over the unlit hemisphere
    const shadowGrad = ctx.createRadialGradient(
      cx - earthRadius * 0.35,
      cy - earthRadius * 0.35,
      earthRadius * 0.2,
      cx + earthRadius * 0.25,
      cy + earthRadius * 0.25,
      earthRadius * 1.15
    );
    shadowGrad.addColorStop(0, "rgba(255, 255, 255, 0.12)"); // Specular highlight
    shadowGrad.addColorStop(0.35, "rgba(0, 0, 0, 0)");
    shadowGrad.addColorStop(0.7, "rgba(2, 6, 23, 0.65)");
    shadowGrad.addColorStop(1, "rgba(2, 6, 23, 0.94)"); // Deep night side

    ctx.fillStyle = shadowGrad;
    ctx.fillRect(cx - earthRadius, cy - earthRadius, earthRadius * 2, earthRadius * 2);

    // 3F. INNER LIMB CYAN RAYLEIGH GLOW
    const limbGrad = ctx.createRadialGradient(
      cx,
      cy,
      earthRadius * 0.78,
      cx,
      cy,
      earthRadius
    );
    limbGrad.addColorStop(0, "rgba(56, 189, 248, 0)");
    limbGrad.addColorStop(0.7, "rgba(56, 189, 248, 0.22)");
    limbGrad.addColorStop(1, "rgba(186, 230, 253, 0.55)");

    ctx.fillStyle = limbGrad;
    ctx.fillRect(cx - earthRadius, cy - earthRadius, earthRadius * 2, earthRadius * 2);

    ctx.restore(); // End Earth Sphere Clip

    // -------------------------------------------------------------
    // 4. ORBIT TRACKS (Front Half - In front of Earth)
    // -------------------------------------------------------------
    if (!isMini) {
      drawOrbitTrack(ctx, cx, cy, earthRadius * 1.48, earthRadius * 0.65, -0.4, false);
      drawOrbitTrack(ctx, cx, cy, earthRadius * 1.58, earthRadius * 0.52, 0.62, false);
    }

    // -------------------------------------------------------------
    // 5. REALISTIC SATELLITES WITH SOLAR PANELS & SCANNING BEAM
    // -------------------------------------------------------------
    // Satellite 1: Sentinel-2 Optical (Polar Orbit)
    const rot1 = -0.4;
    const a1 = earthRadius * 1.48;
    const b1 = earthRadius * 0.65;
    const sX1_u = Math.cos(satAngle1) * a1;
    const sY1_u = Math.sin(satAngle1) * b1;
    const sat1X = cx + sX1_u * Math.cos(rot1) - sY1_u * Math.sin(rot1);
    const sat1Y = cy + sX1_u * Math.sin(rot1) + sY1_u * Math.cos(rot1);
    const sat1Depth = Math.sin(satAngle1); // >0 is front, <0 is back

    // Satellite 2: Sentinel-1 SAR Radar (Inclined Equatorial Orbit)
    const rot2 = 0.62;
    const a2 = earthRadius * 1.58;
    const b2 = earthRadius * 0.52;
    const sX2_u = Math.cos(satAngle2) * a2;
    const sY2_u = Math.sin(satAngle2) * b2;
    const sat2X = cx + sX2_u * Math.cos(rot2) - sY2_u * Math.sin(rot2);
    const sat2Y = cy + sX2_u * Math.sin(rot2) + sY2_u * Math.cos(rot2);
    const sat2Depth = Math.sin(satAngle2);

    // Draw active scanning cone from Sat1 down to Earth when satellite is in front
    if (!isMini && sat1Depth > 0) {
      drawSatelliteSensorBeam(ctx, sat1X, sat1Y, cx, cy, earthRadius, scanPulse);
    }

    // Draw Satellites
    drawRealisticSatellite(ctx, sat1X, sat1Y, sat1Depth, "#38bdf8", isMini);
    if (!isMini) {
      drawRealisticSatellite(ctx, sat2X, sat2Y, sat2Depth, "#c084fc", false);
    }

    // -------------------------------------------------------------
    // ANIMATION STEPPING
    // -------------------------------------------------------------
    earthAngle += 0.007;          // Realistic slow Earth rotation
    cloudAngle += 0.009;          // Clouds drift slightly faster (parallax)
    satAngle1 += isMini ? 0.025 : 0.018; // Orbit speed
    satAngle2 -= 0.014;
    scanPulse += 0.04;

    requestAnimationFrame(renderFrame);
  }

  requestAnimationFrame(renderFrame);
}

/**
 * Projects and fills real continental polygons onto a 3D sphere
 */
function drawContinents(ctx, cx, cy, R, rotAngle) {
  EARTH_CONTINENTS.forEach(poly => {
    ctx.beginPath();
    let hasPoints = false;

    for (let i = 0; i < poly.length; i++) {
      const [lat, lon] = poly[i];
      const latRad = (lat * Math.PI) / 180;
      const lonRad = ((lon + (rotAngle * 180 / Math.PI)) * Math.PI) / 180;

      const cosLat = Math.cos(latRad);
      const sinLat = Math.sin(latRad);
      const cosLon = Math.cos(lonRad);
      const sinLon = Math.sin(lonRad);

      const x = cosLat * sinLon;
      const y = -sinLat; // Invert latitude for canvas Y
      const z = cosLat * cosLon;

      // Only plot vertices on visible hemisphere
      if (z > -0.15) {
        const px = cx + x * R;
        const py = cy + y * R;
        if (!hasPoints) {
          ctx.moveTo(px, py);
          hasPoints = true;
        } else {
          ctx.lineTo(px, py);
        }
      }
    }

    if (hasPoints) {
      ctx.closePath();

      // Realistic vegetation green with terrain variation
      const landGrad = ctx.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
      landGrad.addColorStop(0, "#22c55e"); // Lush temperate / rainforest
      landGrad.addColorStop(0.4, "#16a34a");
      landGrad.addColorStop(0.7, "#ca8a04"); // Savannah / Desert
      landGrad.addColorStop(1, "#15803d");

      ctx.fillStyle = landGrad;
      ctx.fill();

      // Coastal shelf lighter boundary
      ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
      ctx.lineWidth = 0.75;
      ctx.stroke();
    }
  });

  // Ice Caps (North Pole & South Pole)
  drawIceCaps(ctx, cx, cy, R);
}

/**
 * Draws polar permanent ice caps (Greenland / Arctic & Antarctica)
 */
function drawIceCaps(ctx, cx, cy, R) {
  ctx.save();
  // North Pole
  ctx.fillStyle = "rgba(248, 250, 252, 0.85)";
  ctx.beginPath();
  ctx.ellipse(cx, cy - R * 0.88, R * 0.45, R * 0.16, 0, 0, Math.PI * 2);
  ctx.fill();

  // South Pole
  ctx.fillStyle = "rgba(241, 245, 249, 0.9)";
  ctx.beginPath();
  ctx.ellipse(cx, cy + R * 0.88, R * 0.52, R * 0.18, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/**
 * Renders glowing city lights on the night hemisphere
 */
function drawCityLights(ctx, cx, cy, R, rotAngle, Lx, Ly, Lz, isMini) {
  if (isMini) return; // Skip in mini sidebar to conserve draw calls

  NIGHT_CITIES.forEach(([lat, lon, size, intensity]) => {
    const latRad = (lat * Math.PI) / 180;
    const lonRad = ((lon + (rotAngle * 180 / Math.PI)) * Math.PI) / 180;

    const cosLat = Math.cos(latRad);
    const sinLat = Math.sin(latRad);
    const cosLon = Math.cos(lonRad);
    const sinLon = Math.sin(lonRad);

    const x = cosLat * sinLon;
    const y = -sinLat;
    const z = cosLat * cosLon;

    // Only visible on front hemisphere (z > 0.05)
    if (z > 0.05) {
      // Check if this point is in the dark/shadow (N dot L < 0.2)
      const dot = x * Lx + y * Ly + z * Lz;
      if (dot < 0.25) {
        const px = cx + x * R;
        const py = cy + y * R;
        const darknessFactor = Math.min(1, Math.max(0, (0.25 - dot) * 3));
        const alpha = intensity * darknessFactor * 0.85;

        ctx.fillStyle = `rgba(253, 224, 71, ${alpha})`;
        ctx.shadowColor = "#f59e0b";
        ctx.shadowBlur = 4;
        ctx.beginPath();
        ctx.arc(px, py, size * 0.65, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }
  });
}

/**
 * Draws dynamic translucent swirling clouds that drift across Earth
 */
function drawCloudLayer(ctx, cx, cy, R, cloudAngle, isMini) {
  ctx.save();
  ctx.fillStyle = "rgba(255, 255, 255, 0.45)";

  CLOUD_SWIRLS.forEach(([lat, lon, w, h]) => {
    const latRad = (lat * Math.PI) / 180;
    const lonRad = ((lon + (cloudAngle * 180 / Math.PI)) * Math.PI) / 180;

    const cosLat = Math.cos(latRad);
    const sinLat = Math.sin(latRad);
    const cosLon = Math.cos(lonRad);
    const sinLon = Math.sin(lonRad);

    const x = cosLat * sinLon;
    const y = -sinLat;
    const z = cosLat * cosLon;

    if (z > 0.1) {
      const px = cx + x * R;
      const py = cy + y * R;

      ctx.beginPath();
      ctx.ellipse(
        px,
        py,
        (w * R) / 160,
        (h * R) / 180,
        Math.sin(cloudAngle + lat) * 0.4,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
  });

  ctx.restore();
}

/**
 * Draws elliptical orbital tracks
 */
function drawOrbitTrack(ctx, cx, cy, a, b, rotation, isBackHalf) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(rotation);

  ctx.strokeStyle = isBackHalf ? "rgba(56, 189, 248, 0.15)" : "rgba(56, 189, 248, 0.45)";
  ctx.lineWidth = 1;
  ctx.setLineDash([3, 4]);

  ctx.beginPath();
  // Draw full or half ellipse
  ctx.ellipse(0, 0, a, b, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.restore();
}

/**
 * Draws active optical / radar sensor beam scanning the ground
 */
function drawSatelliteSensorBeam(ctx, sx, sy, cx, cy, R, pulse) {
  ctx.save();

  // Target spot on Earth below the satellite
  const targetX = cx + (sx - cx) * 0.45;
  const targetY = cy + (sy - cy) * 0.45;
  const beamWidth = 14 + Math.sin(pulse) * 3;

  // Scanning cone gradient
  const beamGrad = ctx.createLinearGradient(sx, sy, targetX, targetY);
  beamGrad.addColorStop(0, "rgba(56, 189, 248, 0.8)");
  beamGrad.addColorStop(0.3, "rgba(56, 189, 248, 0.25)");
  beamGrad.addColorStop(0.9, "rgba(56, 189, 248, 0.08)");
  beamGrad.addColorStop(1, "rgba(56, 189, 248, 0)");

  ctx.fillStyle = beamGrad;
  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.lineTo(targetX - beamWidth, targetY);
  ctx.lineTo(targetX + beamWidth, targetY);
  ctx.closePath();
  ctx.fill();

  // Glowing footprint ellipse on the Earth surface
  ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
  ctx.beginPath();
  ctx.ellipse(targetX, targetY, beamWidth * 0.8, beamWidth * 0.35, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

/**
 * Renders a high-detail 3D Satellite (Cube body + Solar Arrays + Antennas)
 */
function drawRealisticSatellite(ctx, x, y, depth, themeColor, isMini) {
  ctx.save();
  ctx.translate(x, y);

  // Depth scaling: slightly smaller when behind Earth
  const scale = depth < 0 ? (isMini ? 0.65 : 0.75) : (isMini ? 0.85 : 1.15);
  ctx.scale(scale, scale);

  // If behind Earth, slightly dimmer
  if (depth < 0) {
    ctx.globalAlpha = 0.55;
  }

  // 1. DUAL SOLAR ARRAY WINGS (Blue photovoltaic panels with grid cells)
  const wingW = isMini ? 7 : 14;
  const wingH = isMini ? 3.5 : 6;
  const wingGap = isMini ? 3.5 : 7;

  // Left Solar Wing
  ctx.fillStyle = "#1d4ed8"; // Solar cell deep blue
  ctx.strokeStyle = "rgba(147, 197, 253, 0.8)"; // Silver grid lines
  ctx.lineWidth = 0.7;

  // Left Wing
  ctx.fillRect(-wingGap - wingW, -wingH / 2, wingW, wingH);
  ctx.strokeRect(-wingGap - wingW, -wingH / 2, wingW, wingH);
  // Solar grid dividers
  if (!isMini) {
    ctx.beginPath();
    ctx.moveTo(-wingGap - wingW / 2, -wingH / 2);
    ctx.lineTo(-wingGap - wingW / 2, wingH / 2);
    ctx.moveTo(-wingGap - wingW, 0);
    ctx.lineTo(-wingGap, 0);
    ctx.stroke();
  }

  // Right Solar Wing
  ctx.fillRect(wingGap, -wingH / 2, wingW, wingH);
  ctx.strokeRect(wingGap, -wingH / 2, wingW, wingH);
  if (!isMini) {
    ctx.beginPath();
    ctx.moveTo(wingGap + wingW / 2, -wingH / 2);
    ctx.lineTo(wingGap + wingW / 2, wingH / 2);
    ctx.moveTo(wingGap, 0);
    ctx.lineTo(wingGap + wingW, 0);
    ctx.stroke();
  }

  // Solar Wing Boom Struts
  ctx.strokeStyle = "#cbd5e1";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(-wingGap, 0);
  ctx.lineTo(wingGap, 0);
  ctx.stroke();

  // 2. MAIN SATELLITE BODY (Gold MLI Thermal Foil Cube)
  const bodySize = isMini ? 5 : 9;
  const bodyGrad = ctx.createLinearGradient(-bodySize / 2, -bodySize / 2, bodySize / 2, bodySize / 2);
  bodyGrad.addColorStop(0, "#fde047"); // Specular gold shine
  bodyGrad.addColorStop(0.4, "#f59e0b");
  bodyGrad.addColorStop(1, "#b45309"); // Dark amber gold shadow

  ctx.fillStyle = bodyGrad;
  ctx.strokeStyle = "#fbbf24";
  ctx.lineWidth = 0.8;
  ctx.fillRect(-bodySize / 2, -bodySize / 2, bodySize, bodySize);
  ctx.strokeRect(-bodySize / 2, -bodySize / 2, bodySize, bodySize);

  // 3. EARTH OBSERVATION APERTURE / SAR ANTENNA BOOM
  if (!isMini) {
    ctx.fillStyle = themeColor;
    ctx.beginPath();
    ctx.arc(0, 0, 2, 0, Math.PI * 2);
    ctx.fill();

    // Small SAR Radar boom antenna
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.moveTo(0, bodySize / 2);
    ctx.lineTo(0, bodySize / 2 + 3);
    ctx.stroke();

    // Glowing telemetry LED indicator
    ctx.fillStyle = "#4ade80";
    ctx.shadowColor = "#4ade80";
    ctx.shadowBlur = 6;
    ctx.beginPath();
    ctx.arc(-bodySize / 4, -bodySize / 4, 1, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  ctx.restore();
}

// Automatically mount on DOM ready for both center agent and sidebar
window.addEventListener("DOMContentLoaded", () => {
  // Center Card 3D Earth
  initRealisticEarthCanvas("agentOrbitCanvas", { width: 140, height: 140, isMini: false });

  // Sidebar Mini 3D Earth (if present)
  initRealisticEarthCanvas("sidebarEarthCanvas", { width: 48, height: 48, isMini: true });
});
