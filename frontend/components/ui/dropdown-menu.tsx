"use client"

import * as React from "react"
import { Check, ChevronRight } from "lucide-react"

// Context for root Dropdown
interface DropdownContextType {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
  closeMenu: () => void
}

const DropdownContext = React.createContext<DropdownContextType>({
  open: false,
  setOpen: () => {},
  closeMenu: () => {},
})

export function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  const menuRef = React.useRef<HTMLDivElement>(null)

  const closeMenu = React.useCallback(() => setOpen(false), [])

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      document.addEventListener("keydown", handleKeyDown)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.removeEventListener("keydown", handleKeyDown)
    }
  }, [open])

  return (
    <DropdownContext.Provider value={{ open, setOpen, closeMenu }}>
      <div ref={menuRef} style={{ position: "relative", display: "inline-block" }}>
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

export function DropdownMenuTrigger({
  asChild = false,
  children,
  ...props
}: {
  asChild?: boolean
  children: React.ReactNode
  [key: string]: unknown
}) {
  const { open, setOpen } = React.useContext(DropdownContext)

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setOpen((prev) => !prev)
  }

  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<{
      onClick?: (e: React.MouseEvent) => void
      "aria-expanded"?: boolean
    }>
    return React.cloneElement(child, {
      onClick: (e: React.MouseEvent) => {
        child.props.onClick?.(e)
        handleClick(e)
      },
      "aria-expanded": open,
      ...props,
    })
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-expanded={open}
      style={{
        background: "none",
        border: "none",
        padding: 0,
        cursor: "pointer",
        outline: "none",
      }}
      {...props}
    >
      {children}
    </button>
  )
}

export function DropdownMenuContent({
  align = "start",
  className = "",
  style,
  children,
  ...props
}: {
  align?: "start" | "center" | "end"
  className?: string
  style?: React.CSSProperties
  children: React.ReactNode
  [key: string]: unknown
}) {
  const { open } = React.useContext(DropdownContext)

  if (!open) return null

  let alignStyle: React.CSSProperties = { left: 0 }
  if (align === "end") {
    alignStyle = { right: 0, left: "auto" }
  } else if (align === "center") {
    alignStyle = { left: "50%", transform: "translateX(-50%)" }
  }

  return (
    <div
      className={`aletheia-dropdown-content ${className}`.trim()}
      role="menu"
      style={{
        position: "absolute",
        top: "calc(100% + 4px)",
        zIndex: 100,
        minWidth: "180px",
        backgroundColor: "#161614",
        border: "1px solid #2e2c26",
        borderRadius: "6px",
        padding: "4px",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
        backdropFilter: "blur(12px)",
        ...alignStyle,
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  )
}

export function DropdownMenuGroup({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>{children}</div>
}

export function DropdownMenuItem({
  variant = "default",
  className = "",
  children,
  onClick,
  style,
  ...props
}: {
  variant?: "default" | "destructive"
  className?: string
  children: React.ReactNode
  onClick?: (e: React.MouseEvent) => void
  style?: React.CSSProperties
  [key: string]: unknown
}) {
  const { closeMenu } = React.useContext(DropdownContext)

  const isDestructive = variant === "destructive"

  return (
    <div
      role="menuitem"
      tabIndex={0}
      className={`aletheia-dropdown-item ${className}`.trim()}
      onClick={(e) => {
        onClick?.(e)
        closeMenu()
      }}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        padding: "6px 8px",
        fontSize: "0.8125rem",
        borderRadius: "4px",
        cursor: "pointer",
        color: isDestructive ? "var(--signal-failure)" : "var(--text-secondary)",
        transition: "all 0.1s ease",
        userSelect: "none",
        ...style,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = isDestructive
          ? "rgba(196, 104, 93, 0.12)"
          : "rgba(231, 227, 220, 0.05)"
        if (!isDestructive) e.currentTarget.style.color = "var(--text-primary)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "transparent"
        if (!isDestructive) e.currentTarget.style.color = "var(--text-secondary)"
      }}
      {...props}
    >
      {children}
    </div>
  )
}

export function DropdownMenuSeparator() {
  return (
    <div
      style={{
        height: "1px",
        backgroundColor: "rgba(231, 227, 220, 0.07)",
        margin: "4px -4px",
      }}
    />
  )
}

// Submenu context
interface SubContextType {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
}
const SubContext = React.createContext<SubContextType>({ open: false, setOpen: () => {} })

export function DropdownMenuSub({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  return (
    <SubContext.Provider value={{ open, setOpen }}>
      <div
        style={{ position: "relative" }}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        {children}
      </div>
    </SubContext.Provider>
  )
}

export function DropdownMenuSubTrigger({
  children,
  className = "",
  style,
  ...props
}: {
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  [key: string]: unknown
}) {
  const { open } = React.useContext(SubContext)

  return (
    <div
      className={`aletheia-dropdown-item ${className}`.trim()}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "8px",
        padding: "6px 8px",
        fontSize: "0.8125rem",
        borderRadius: "4px",
        cursor: "pointer",
        color: "var(--text-secondary)",
        backgroundColor: open ? "rgba(231, 227, 220, 0.05)" : "transparent",
        userSelect: "none",
        ...style,
      }}
      {...props}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>{children}</div>
      <ChevronRight size={14} style={{ color: "var(--text-muted)" }} />
    </div>
  )
}

export function DropdownMenuSubContent({
  children,
  className = "",
  style,
  ...props
}: {
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  [key: string]: unknown
}) {
  const { open } = React.useContext(SubContext)
  if (!open) return null

  return (
    <div
      className={`aletheia-dropdown-content ${className}`.trim()}
      style={{
        position: "absolute",
        left: "calc(100% + 2px)",
        top: "-4px",
        zIndex: 110,
        minWidth: "150px",
        backgroundColor: "#161614",
        border: "1px solid #2e2c26",
        borderRadius: "6px",
        padding: "4px",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
        backdropFilter: "blur(12px)",
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  )
}

// Radio group
interface RadioContextType {
  value: string
  onValueChange: (val: string) => void
}
const RadioContext = React.createContext<RadioContextType>({
  value: "",
  onValueChange: () => {},
})

export function DropdownMenuRadioGroup({
  value,
  onValueChange,
  children,
}: {
  value: string
  onValueChange: (val: string) => void
  children: React.ReactNode
}) {
  return (
    <RadioContext.Provider value={{ value, onValueChange }}>
      <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>{children}</div>
    </RadioContext.Provider>
  )
}

export function DropdownMenuRadioItem({
  value,
  children,
  className = "",
  style,
  ...props
}: {
  value: string
  children: React.ReactNode
  className?: string
  style?: React.CSSProperties
  [key: string]: unknown
}) {
  const { value: selectedValue, onValueChange } = React.useContext(RadioContext)
  const isSelected = selectedValue === value

  return (
    <div
      role="menuitemradio"
      aria-checked={isSelected}
      className={`aletheia-dropdown-item ${className}`.trim()}
      onClick={() => onValueChange(value)}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "6px 8px",
        fontSize: "0.8125rem",
        borderRadius: "4px",
        cursor: "pointer",
        color: isSelected ? "var(--text-primary)" : "var(--text-secondary)",
        backgroundColor: isSelected ? "rgba(143, 165, 138, 0.12)" : "transparent",
        userSelect: "none",
        ...style,
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = "rgba(231, 227, 220, 0.05)"
          e.currentTarget.style.color = "var(--text-primary)"
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = "transparent"
          e.currentTarget.style.color = "var(--text-secondary)"
        }
      }}
      {...props}
    >
      <span>{children}</span>
      {isSelected && <Check size={14} style={{ color: "var(--accent-sage)" }} />}
    </div>
  )
}
