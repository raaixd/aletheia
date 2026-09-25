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
          backgroundColor: "#181816",
          borderColor: "#2e2c26",
          color: "#e7e3dc",
        }
        break
      case "ghost":
        variantStyle = {
          backgroundColor: "transparent",
          borderColor: "transparent",
          color: "#b7b2a9",
        }
        break
      case "secondary":
        variantStyle = {
          backgroundColor: "#20201d",
          borderColor: "#33312b",
          color: "#e7e3dc",
        }
        break
      case "destructive":
        variantStyle = {
          backgroundColor: "rgba(196, 104, 93, 0.14)",
          borderColor: "rgba(196, 104, 93, 0.35)",
          color: "#f7d5d1",
        }
        break
      case "default":
      default:
        variantStyle = {
          backgroundColor: "#262521",
          borderColor: "#3d3a33",
          color: "#e7e3dc",
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
