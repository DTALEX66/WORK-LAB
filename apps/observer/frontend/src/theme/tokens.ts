/**
 * UI_TOKENS (20260921): single source of truth for WORK-LAB Observer theme
 * values. The CSS variable blocks in src/index.css MUST mirror these exact
 * values (asserted by tokens.test.ts). Authority: .ui-reference/WORK-LAB/
 * 10_B10 (visual supreme), L4 WORK-LAB_design_tokens.json, L7 theme/tokens.json
 * — three-way identical.
 *
 * Accent colors are RGB channel triples ("42 145 255") because index.css
 * defines them as `rgb(var(--X-rgb) / <alpha-value>)` for Tailwind alpha
 * modifiers. Surfaces are hex strings.
 */

export type ThemeAccentKey =
  | "primary"
  | "secondary"
  | "success"
  | "warning"
  | "error"
  | "info";

export interface ThemeColors {
  bg: string;
  sidebar: string;
  panel: string;
  panel2: string;
  border: string;
  ink: string;
  muted: string;
  /** hex, for reference/tests */
  primaryHex: string;
  secondaryHex: string;
  successHex: string;
  warningHex: string;
  errorHex: string;
  infoHex: string;
}

export interface ThemeValues {
  /**
   * RGB channel triples matching index.css `--X-rgb` variables exactly.
   * Keyed by accent name (primary/secondary/success/warning/error/info).
   */
  accents: Record<ThemeAccentKey, string>;
  colors: ThemeColors;
  radius: { sm: string; md: string; lg: string; xl: string };
  shadow: string;
  glassBlur: string;
  motion: {
    fast: string;
    base: string;
    modal: string;
    drawer: string;
    emphasis: string;
    pressed: string;
  };
  density: { comfortable: string; default: string; compact: string };
}

export const DARK: ThemeValues = {
  accents: {
    primary: "42 145 255",
    secondary: "32 205 225",
    success: "34 197 94",
    warning: "245 158 11",
    error: "239 68 68",
    info: "56 130 246",
  },
  colors: {
    bg: "#050D16",
    sidebar: "#07111C",
    panel: "#081420",
    panel2: "#0C1B2A",
    border: "#17435D",
    ink: "#EEF6FC",
    muted: "#8EABBC",
    primaryHex: "#2A91FF",
    secondaryHex: "#20CDE1",
    successHex: "#22C55E",
    warningHex: "#F59E0B",
    errorHex: "#EF4444",
    infoHex: "#3882F6",
  },
  radius: { sm: "4px", md: "10px", lg: "16px", xl: "22px" },
  shadow: "0 20px 80px rgba(0, 0, 0, 0.35)",
  glassBlur: "18px",
  motion: {
    fast: "120ms",
    base: "180ms",
    modal: "220ms",
    drawer: "280ms",
    emphasis: "420ms",
    pressed: "80ms",
  },
  density: { comfortable: "68px", default: "56px", compact: "44px" },
};

export const LIGHT: ThemeValues = {
  accents: {
    primary: "27 127 230",
    secondary: "14 147 165",
    success: "21 128 61",
    warning: "180 83 9",
    error: "185 28 28",
    info: "29 78 216",
  },
  colors: {
    bg: "#F4F7FA",
    sidebar: "#E4EBF2",
    panel: "#FFFFFF",
    panel2: "#EAF0F6",
    border: "#D5E2EC",
    ink: "#0B1420",
    muted: "#5A7184",
    primaryHex: "#1B7FE6",
    secondaryHex: "#0E93A5",
    successHex: "#15803D",
    warningHex: "#B45309",
    errorHex: "#B91C1C",
    infoHex: "#1D4ED8",
  },
  radius: DARK.radius,
  shadow: DARK.shadow,
  glassBlur: DARK.glassBlur,
  motion: DARK.motion,
  density: DARK.density,
};

export const THEMES: Record<"dark" | "light", ThemeValues> = {
  dark: DARK,
  light: LIGHT,
};
