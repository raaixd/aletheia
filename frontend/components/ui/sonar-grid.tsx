"use client";

import React, { useEffect, useRef, useCallback } from "react";

interface Ring {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  speed: number;
  alpha: number;
  thickness: number;
}

export interface SonarGridProps {
  gridSize?: number;
  dotRadius?: number;
  dotColor?: string;
  activeColor?: string;
  ringColor?: string;
  pingIntervalMs?: number;
  className?: string;
  interactive?: boolean;
}

export function SonarGrid({
  gridSize = 34,
  dotRadius = 1,
  dotColor = "rgba(148, 163, 184, 0.12)",
  activeColor = "rgba(59, 130, 246, 0.55)",
  ringColor = "rgba(37, 99, 235, 0.18)",
  pingIntervalMs = 4200,
  className = "",
  interactive = true,
}: SonarGridProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const ringsRef = useRef<Ring[]>([]);
  const animFrameIdRef = useRef<number | null>(null);
  const isVisibleRef = useRef<boolean>(true);
  const prefersReducedMotionRef = useRef<boolean>(false);

  // Spawns a new expanding ring
  const spawnRing = useCallback((x: number, y: number, initialRadius = 0) => {
    if (prefersReducedMotionRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const maxRadius = Math.max(canvas.width, canvas.height) * 0.75;
    ringsRef.current.push({
      x,
      y,
      radius: initialRadius,
      maxRadius,
      speed: 1.25,
      alpha: 1.0,
      thickness: 38,
    });
  }, []);

  useEffect(() => {
    // Check prefers-reduced-motion
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    prefersReducedMotionRef.current = motionQuery.matches;

    const handleMotionChange = (e: MediaQueryListEvent) => {
      prefersReducedMotionRef.current = e.matches;
    };
    motionQuery.addEventListener("change", handleMotionChange);

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let width = 0;
    let height = 0;
    const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1, 2);

    const resize = () => {
      const rect = container.getBoundingClientRect();
      width = rect.width;
      height = rect.height;

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.scale(dpr, dpr);
    };

    resize();

    // Pre-seed one mid-flight ring so initial paint is dynamic
    if (!prefersReducedMotionRef.current && width > 0) {
      spawnRing(width * 0.5, height * 0.45, 120);
    }

    const resizeObserver = new ResizeObserver(() => {
      resize();
    });
    resizeObserver.observe(container);

    // Track intersection to avoid background rendering
    const intersectionObserver = new IntersectionObserver(([entry]) => {
      isVisibleRef.current = entry.isIntersecting;
      if (entry.isIntersecting && !animFrameIdRef.current) {
        lastTime = performance.now();
        render();
      }
    });
    intersectionObserver.observe(container);

    // Handle tab visibility
    const handleVisibilityChange = () => {
      if (document.hidden) {
        isVisibleRef.current = false;
        if (animFrameIdRef.current) {
          cancelAnimationFrame(animFrameIdRef.current);
          animFrameIdRef.current = null;
        }
      } else {
        isVisibleRef.current = true;
        lastTime = performance.now();
        render();
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // Ambient ping interval
    const pingTimer = setInterval(() => {
      if (isVisibleRef.current && !prefersReducedMotionRef.current && width > 0) {
        spawnRing(width * 0.5, height * 0.45, 0);
      }
    }, pingIntervalMs);

    let lastTime = performance.now();

    const render = () => {
      if (!isVisibleRef.current) {
        animFrameIdRef.current = null;
        return;
      }

      const now = performance.now();
      const delta = Math.min((now - lastTime) / 16.666, 2.5); // normalized frame delta
      lastTime = now;

      ctx.clearRect(0, 0, width, height);

      // Advance and filter rings
      if (!prefersReducedMotionRef.current) {
        for (let i = ringsRef.current.length - 1; i >= 0; i--) {
          const r = ringsRef.current[i];
          r.radius += r.speed * delta;
          r.alpha = Math.max(0, 1 - r.radius / r.maxRadius);

          if (r.radius >= r.maxRadius || r.alpha <= 0) {
            ringsRef.current.splice(i, 1);
          }
        }
      }

      const currentRings = ringsRef.current;

      // Draw faint ring strokes
      for (let i = 0; i < currentRings.length; i++) {
        const r = currentRings[i];
        if (r.radius > 5 && r.alpha > 0.01) {
          ctx.beginPath();
          ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
          ctx.strokeStyle = ringColor.replace(/[\d.]+\)$/, `${(0.18 * r.alpha).toFixed(3)})`);
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }

      // Draw the technical dot grid
      const cols = Math.ceil(width / gridSize) + 1;
      const rows = Math.ceil(height / gridSize) + 1;
      const offsetX = (width % gridSize) / 2;
      const offsetY = (height % gridSize) / 2;

      for (let col = 0; col < cols; col++) {
        const x = offsetX + col * gridSize;

        for (let row = 0; row < rows; row++) {
          const y = offsetY + row * gridSize;

          // Determine signal wave illumination from all active rings
          let intensity = 0;

          if (!prefersReducedMotionRef.current) {
            for (let i = 0; i < currentRings.length; i++) {
              const r = currentRings[i];
              const dist = Math.hypot(x - r.x, y - r.y);
              const deltaDist = Math.abs(dist - r.radius);

              if (deltaDist < r.thickness) {
                const waveProximity = 1 - deltaDist / r.thickness;
                intensity = Math.max(intensity, waveProximity * r.alpha);
              }
            }
          }

          ctx.beginPath();
          ctx.arc(x, y, dotRadius + (intensity > 0.2 ? 0.35 : 0), 0, Math.PI * 2);

          if (intensity > 0.05) {
            // Signal-illuminated dot
            ctx.fillStyle = activeColor.replace(
              /[\d.]+\)$/,
              `${(0.15 + intensity * 0.55).toFixed(3)})`
            );
          } else {
            // Resting dot
            ctx.fillStyle = dotColor;
          }

          ctx.fill();
        }
      }

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      clearInterval(pingTimer);
      motionQuery.removeEventListener("change", handleMotionChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, [gridSize, dotRadius, dotColor, activeColor, ringColor, pingIntervalMs, spawnRing]);

  // Click interaction emitting a subtle signal pulse
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!interactive || prefersReducedMotionRef.current) return;
    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    spawnRing(x, y, 0);
  };

  return (
    <div
      ref={containerRef}
      onClick={handleClick}
      aria-hidden="true"
      className={`absolute inset-0 pointer-events-auto ${className}`}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: "hidden",
        zIndex: 0,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          display: "block",
          width: "100%",
          height: "100%",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
