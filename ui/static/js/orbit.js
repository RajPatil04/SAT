/**
 * SatQuery Agent - Holographic Earth & Satellite Orbital Canvas
 * Renders an interactive, glowing Earth globe with orbital tracks and satellites.
 */

function initOrbitCanvas(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let width = (canvas.width = canvas.parentElement.clientWidth || 140);
  let height = (canvas.height = 140);

  let angle = 0;
  let satAngle1 = 0;
  let satAngle2 = Math.PI * 0.75;

  function render() {
    ctx.clearRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2;
    const radius = 38;

    // 1. Outer Atmospheric Glow
    const glowGrad = ctx.createRadialGradient(cx, cy, radius * 0.7, cx, cy, radius * 1.55);
    glowGrad.addColorStop(0, "rgba(56, 189, 248, 0.45)");
    glowGrad.addColorStop(0.5, "rgba(37, 99, 235, 0.2)");
    glowGrad.addColorStop(1, "rgba(7, 11, 20, 0)");
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.55, 0, Math.PI * 2);
    ctx.fill();

    // 2. Earth Sphere Base
    const sphereGrad = ctx.createRadialGradient(
      cx - radius * 0.35,
      cy - radius * 0.35,
      radius * 0.1,
      cx,
      cy,
      radius
    );
    sphereGrad.addColorStop(0, "#38bdf8");
    sphereGrad.addColorStop(0.3, "#1d4ed8");
    sphereGrad.addColorStop(0.8, "#0f172a");
    sphereGrad.addColorStop(1, "#030712");

    ctx.fillStyle = sphereGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();

    // 3. Latitude & Longitude Holographic Grid Rings
    ctx.save();
    ctx.strokeStyle = "rgba(147, 197, 253, 0.35)";
    ctx.lineWidth = 1;

    // Equator / Latitude arcs
    for (let lat = -20; lat <= 20; lat += 20) {
      ctx.beginPath();
      const latY = cy + Math.sin((lat * Math.PI) / 180) * radius * 0.8;
      const latR = Math.cos((lat * Math.PI) / 180) * radius;
      ctx.ellipse(cx, latY, latR, latR * 0.28, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Rotating Longitude meridian
    ctx.beginPath();
    const lonW = Math.abs(Math.cos(angle)) * radius;
    ctx.ellipse(cx, cy, lonW, radius, 0, 0, Math.PI * 2);
    ctx.stroke();

    ctx.restore();

    // 4. Orbital Track 1 (Inclined Polar / SSO Orbit)
    ctx.save();
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 1.2;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.ellipse(cx, cy, radius * 1.42, radius * 0.65, -0.45, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // 5. Satellite 1 on Orbit Track 1
    const rot = -0.45;
    const a1 = radius * 1.42;
    const b1 = radius * 0.65;
    const sX1_unrot = Math.cos(satAngle1) * a1;
    const sY1_unrot = Math.sin(satAngle1) * b1;
    const sX1 = cx + sX1_unrot * Math.cos(rot) - sY1_unrot * Math.sin(rot);
    const sY1 = cy + sX1_unrot * Math.sin(rot) + sY1_unrot * Math.cos(rot);

    // Draw Satellite 1
    drawSatelliteIcon(ctx, sX1, sY1, "#38bdf8");

    // 6. Orbital Track 2 (Equatorial / MEO Orbit)
    ctx.save();
    ctx.strokeStyle = "rgba(168, 85, 247, 0.3)";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);
    ctx.beginPath();
    ctx.ellipse(cx, cy, radius * 1.5, radius * 0.5, 0.65, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    // Satellite 2
    const rot2 = 0.65;
    const a2 = radius * 1.5;
    const b2 = radius * 0.5;
    const sX2_unrot = Math.cos(satAngle2) * a2;
    const sY2_unrot = Math.sin(satAngle2) * b2;
    const sX2 = cx + sX2_unrot * Math.cos(rot2) - sY2_unrot * Math.sin(rot2);
    const sY2 = cy + sX2_unrot * Math.sin(rot2) + sY2_unrot * Math.cos(rot2);

    drawSatelliteIcon(ctx, sX2, sY2, "#c084fc");

    // Step animations
    angle += 0.015;
    satAngle1 += 0.022;
    satAngle2 -= 0.016;

    requestAnimationFrame(render);
  }

  function drawSatelliteIcon(c, x, y, color) {
    c.save();
    // Glow
    c.shadowColor = color;
    c.shadowBlur = 8;
    c.fillStyle = color;
    
    // Core body
    c.fillRect(x - 2.5, y - 2.5, 5, 5);

    // Solar panels
    c.fillStyle = "#ffffff";
    c.fillRect(x - 7, y - 1, 3.5, 2);
    c.fillRect(x + 3.5, y - 1, 3.5, 2);

    c.restore();
  }

  requestAnimationFrame(render);
}

window.addEventListener("DOMContentLoaded", () => {
  initOrbitCanvas("agentOrbitCanvas");
});
