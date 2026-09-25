"use client";

import React from "react";

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  borderWidth?: number;
  colorFrom?: string;
  colorTo?: string;
  delay?: number;
  isActive?: boolean;
}

export function BorderBeam({
  className = "",
  size = 120,
  duration = 7,
  borderWidth = 1.5,
  colorFrom = "#3b82f6",
  colorTo = "#10b981",
  delay = 0,
  isActive = true,
}: BorderBeamProps) {
  if (!isActive) return null;

  return (
    <div
      aria-hidden="true"
      style={
        {
          pointerEvents: "none",
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          border: `${borderWidth}px solid transparent`,
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          maskComposite: "exclude",
          WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMaskComposite: "xor",
          "--size": `${size}px`,
          "--duration": `${duration}s`,
          "--delay": `-${delay}s`,
          "--color-from": colorFrom,
          "--color-to": colorTo,
        } as React.CSSProperties
      }
      className={`aletheia-border-beam ${className}`.trim()}
    />
  );
}
