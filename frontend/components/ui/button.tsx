"use client"

import * as React from "react"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "secondary" | "destructive"
  size?: "default" | "sm" | "lg" | "icon"
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = "",
      variant = "default",
      size = "default",
      asChild = false,
      children,
      style,
      ...props
    },
    ref
  ) => {
    // Base inline styles matching our design system tokens
    const baseStyle: React.CSSProperties = {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "8px",
      whiteSpace: "nowrap",
      fontFamily: "var(--font-sans, inherit)",
      fontSize: size === "sm" ? "0.75rem" : size === "lg" ? "0.9375rem" : "0.8125rem",
      fontWeight: 500,
      borderRadius: "4px",
      transition: "all 0.15s ease",
      cursor: props.disabled ? "not-allowed" : "pointer",
      opacity: props.disabled ? 0.5 : 1,
      outline: "none",
      border: "1px solid transparent",
      textDecoration: "none",
      userSelect: "none",
    }

    // Size variants
    const sizeStyle: React.CSSProperties =
      size === "icon"
        ? { width: "32px", height: "32px", padding: "0" }
        : size === "sm"
        ? { height: "28px", padding: "0 10px" }
        : size === "lg"
        ? { height: "40px", padding: "0 18px" }
        : { height: "32px", padding: "0 14px" }

    // Color variants
    let variantStyle: React.CSSProperties = {}
    let variantClass = "aletheia-btn-" + variant

    switch (variant) {
      case "outline":
        variantStyle = {
          backgroundColor: "rgba(14, 18, 27, 0.75)",
          borderColor: "rgba(255, 255, 255, 0.12)",
          color: "#e2e8f0",
        }
        break
      case "ghost":
        variantStyle = {
          backgroundColor: "transparent",
          borderColor: "transparent",
          color: "#94a3b8",
        }
        break
      case "secondary":
        variantStyle = {
          backgroundColor: "#161d2d",
          borderColor: "rgba(255, 255, 255, 0.08)",
          color: "#f1f5f9",
        }
        break
      case "destructive":
        variantStyle = {
          backgroundColor: "rgba(225, 29, 72, 0.12)",
          borderColor: "rgba(225, 29, 72, 0.35)",
          color: "#fda4af",
        }
        break
      case "default":
      default:
        variantStyle = {
          backgroundColor: "#1d4ed8",
          borderColor: "#2563eb",
          color: "#ffffff",
        }
        break
    }

    const mergedStyle: React.CSSProperties = {
      ...baseStyle,
      ...sizeStyle,
      ...variantStyle,
      ...style,
    }

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{
        className?: string
        style?: React.CSSProperties
        ref?: React.Ref<unknown>
      }>
      return React.cloneElement(child, {
        ref,
        className: `${className} ${variantClass} ${child.props.className || ""}`.trim(),
        style: { ...mergedStyle, ...child.props.style },
        ...props,
      })
    }

    return (
      <button
        ref={ref}
        className={`aletheia-button ${variantClass} ${className}`.trim()}
        style={mergedStyle}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = "Button"
