"use client"

import * as React from "react"

export interface ButtonGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode
  orientation?: "horizontal" | "vertical"
}

export function ButtonGroup({
  className = "",
  orientation = "horizontal",
  children,
  style,
  ...props
}: ButtonGroupProps) {
  return (
    <div
      className={`aletheia-button-group ${orientation} ${className}`.trim()}
      role="group"
      style={{
        display: "inline-flex",
        flexDirection: orientation === "vertical" ? "column" : "row",
        alignItems: "center",
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  )
}
