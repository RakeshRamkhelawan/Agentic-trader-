import * as React from "react"
import { cn } from "@/lib/utils"

const GlassCard = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn(
            "glass-card rounded-xl p-6 text-card-foreground shadow-sm",
            className
        )}
        {...props}
    />
))
GlassCard.displayName = "GlassCard"

export { GlassCard }
