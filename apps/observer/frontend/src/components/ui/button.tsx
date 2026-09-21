import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * UI_COMPONENTS (20260921): shared Button from the L4/L6 interaction authority.
 * hover 120-180ms (transitionDuration base), pressed scale(.99) 80ms
 * (active:scale + transition-duration fast/pressed), focus-visible ring 2px
 * primary offset 2px. All colors resolve through the SPEC-A CSS variables.
 */
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-md font-medium select-none ' +
  'transition-[background-color,border-color,box-shadow,transform,opacity] duration-base ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 ' +
  'focus-visible:ring-offset-bg active:scale-[0.99] active:duration-fast ' +
  'disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-white hover:bg-primary/90 shadow-card',
        secondary: 'bg-secondary/15 text-secondary border border-secondary/30 hover:bg-secondary/25',
        ghost: 'bg-transparent text-ink hover:bg-panel2 border border-transparent hover:border-border',
        danger: 'bg-error/15 text-error border border-error/30 hover:bg-error/25',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-5 text-base',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  iconLeft?: LucideIcon
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, iconLeft: Icon, children, type = 'button', ...props }, ref) => (
    <button
      ref={ref}
      type={type}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {Icon ? <Icon className="h-4 w-4" aria-hidden="true" /> : null}
      {children}
    </button>
  ),
)
Button.displayName = 'Button'

export { Button, buttonVariants }
