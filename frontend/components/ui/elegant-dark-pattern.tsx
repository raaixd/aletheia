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
        backgroundColor: "#0f0f0e",
        color: "#e7e3dc",
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
            radial-gradient(circle 900px at 50% -120px, rgba(143, 165, 138, 0.04), transparent 70%),
            radial-gradient(circle, rgba(231, 227, 220, 0.02) 1px, transparent 1px)
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
