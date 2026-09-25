"use client";

import React from "react";

interface DarkGradientBgProps {
  children?: React.ReactNode;
  className?: string;
}

export function DarkGradientBg({ children, className = "" }: DarkGradientBgProps) {
  return (
    <div
      className={`relative min-h-screen w-full bg-[#08090c] text-[#f4f4f6] overflow-x-hidden ${className}`}
      style={{
        backgroundColor: "#08090c",
      }}
    >
      {/* Layer 1: Ambient Depth Radial Gradients */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage: `
            radial-gradient(circle 900px at 50% -120px, rgba(37, 99, 235, 0.12), transparent 70%),
            radial-gradient(circle 650px at 85% 15%, rgba(16, 185, 129, 0.05), transparent 60%),
            radial-gradient(circle 700px at 15% 45%, rgba(30, 41, 59, 0.18), transparent 65%),
            radial-gradient(circle 900px at 50% 100%, rgba(15, 23, 42, 0.22), transparent 70%)
          `,
        }}
      />

      {/* Layer 2: Subtle Geometric Dot Matrix */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.03]"
        style={{
          backgroundImage: `radial-gradient(circle, #ffffff 1px, transparent 1px)`,
          backgroundSize: "32px 32px",
        }}
      />

      {/* Layer 3: Faint Technical Grid Lines */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: "96px 96px",
        }}
      />

      {/* Layer 4: Micro Grain Texture Filter */}
      <svg
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-[0.018] mix-blend-overlay"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="dark-grain-noise">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#dark-grain-noise)" />
      </svg>

      {/* Layer 5: Edge Vignette */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(6, 7, 10, 0.6) 100%)",
        }}
      />

      {/* Main Content Layer */}
      <div className="relative z-10 w-full min-h-screen">
        {children}
      </div>
    </div>
  );
}
