"use client"

import React from "react"

interface DarkGradientBgProps {
  children?: React.ReactNode
  className?: string
}

export function DarkGradientBg({ children, className = "" }: DarkGradientBgProps) {
  return (
    <div
      className={`relative min-h-screen w-full bg-[#08090d] text-[#f8fafc] overflow-x-hidden ${className}`}
      style={{
        backgroundColor: "#07080c",
      }}
    >
      {/* Layer 1: Ambient Radial Mesh Gradients */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage: `
            radial-gradient(circle 900px at 50% -100px, rgba(30, 58, 102, 0.22), transparent 70%),
            radial-gradient(circle 700px at 85% 20%, rgba(20, 35, 60, 0.16), transparent 60%),
            radial-gradient(circle 600px at 15% 50%, rgba(14, 25, 45, 0.18), transparent 60%),
            radial-gradient(circle 800px at 50% 100%, rgba(10, 18, 32, 0.25), transparent 70%)
          `,
        }}
      />

      {/* Layer 2: Subtle Geometric Dot/Grid Overlay */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.035]"
        style={{
          backgroundImage: `radial-gradient(circle, #ffffff 1px, transparent 1px)`,
          backgroundSize: "28px 28px",
        }}
      />

      {/* Layer 3: Ultra-fine Grain / Texture Pattern */}
      <svg
        className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-[0.022] mix-blend-overlay"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="dark-grain-noise">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.75"
            numOctaves="3"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#dark-grain-noise)" />
      </svg>

      {/* Layer 4: Deep Obsidian Vignette */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(5, 6, 9, 0.65) 100%)",
        }}
      />

      {/* Main Content Layer */}
      <div className="relative z-10 w-full min-h-screen">
        {children}
      </div>
    </div>
  )
}
