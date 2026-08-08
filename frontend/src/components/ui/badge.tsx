import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[var(--color-cyber-accent)]/20 text-[var(--color-cyber-accent)] hover:bg-[var(--color-cyber-accent)]/30",
        secondary:
          "border-transparent bg-[var(--color-cyber-border)] text-[var(--color-cyber-text)] hover:bg-[var(--color-cyber-border)]/80",
        destructive:
          "border-transparent bg-[var(--color-cyber-danger)]/20 text-[var(--color-cyber-danger)] hover:bg-[var(--color-cyber-danger)]/30",
        outline: "text-[var(--color-cyber-text)] border-[var(--color-cyber-border)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
