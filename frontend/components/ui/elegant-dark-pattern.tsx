"use client";

import React from "react";

interface DarkGradientBgProps {
  children?: React.ReactNode;
  className?: string;
}

export function DarkGradientBg({ children, className = "" }: DarkGradientBgProps) {
  return (
    <div
      style={{
        position: "relative",
        minHeight: "100vh",
        width: "100%",
        backgroundColor: "#08090c",
        color: "#f4f4f6",
      }}
      className={className}
    >
      {/* Ambient Depth Background: Fixed, Zero In-flow Space, Zero Render Artifacts */}
      <div
        aria-hidden="true"
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          zIndex: 0,
          backgroundImage: `
            radial-gradient(circle 800px at 50% -80px, rgba(37, 99, 235, 0.08), transparent 70%),
            radial-gradient(circle, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "auto, 28px 28px",
        }}
      />

      {/* Main Content Layer */}
      <div style={{ position: "relative", zIndex: 1, minHeight: "100vh" }}>
        {children}
      </div>
    </div>
  );
}
