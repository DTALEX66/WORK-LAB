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
  // sm is the pinned skin's value: skins/b10.css declares --radius-sm:12px and loads after index.css, so
  // 12px is what every consumer renders. scripts/ci/verify_css_token_mirror.py keeps the two in step.
  radius: { sm: "12px", md: "10px", lg: "16px", xl: "22px" },
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
    // index.css html.light moved this channel to 154 74 5 (#9A4A05) because amber as light text
    // measured 4.48:1; the same channel feeds the text role, so the record has to carry the readable one.
    warning: "154 74 5",
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
    // The AA value index.css and skins/l10b-shell.css both ship for the light muted role. #5A7184 lived here
    // after that fix and still reached the DOM: TopStatusBar paints its status dot from THEMES[theme].colors,
    // so the light theme showed one grey in the chrome and another in every label.
    muted: "#4A6172",
    primaryHex: "#1B7FE6",
    secondaryHex: "#0E93A5",
    successHex: "#15803D",
    warningHex: "#9A4A05",
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

/**
 * The read-only iron law, machine-readable — the visual layer's share of the
 * authority chain (Observer projects, it never acts).
 *
 * assets/brand/design-tokens.json carries the same three values for consumers
 * that do not read TypeScript; the production-surface static contract compares
 * the two and fails on a disagreement, so this cannot drift into a decoration.
 */
export const VIEW_CONSTRAINTS = {
  readOnly: true,
  externalMutation: false,
  modelSummary: false,
} as const;

/* --------------------------------------------------------------------------
 * WUI-03 (20261009) · palettes.
 *
 * The 20261009 UI pack carries its own colour sheet. Per the owner's decision it does NOT replace the
 * shipped colours — the shipped pair above stays what a fresh session renders, and the pack's values
 * become a selectable palette (`?palette=master`). `src/index.css` declares the same numbers under
 * `html[data-palette="master"]`; src/theme/paletteMirror.contract.test.ts compares the two and fails on
 * a drift, and it also re-pins DARK/LIGHT so an overwrite would have to be deliberate.
 * ------------------------------------------------------------------------ */

export type PaletteId = "worklab" | "master";

/** What a session renders with no `?palette=` in the address. */
export const DEFAULT_PALETTE_ID: PaletteId = "worklab";

export interface PaletteSurface {
  bg: string;
  sidebar: string;
  panel: string;
  panel2: string;
  border: string;
  ink: string;
  muted: string;
}

/** The channels the pack names. It names no secondary (cyan) and no info, so neither appears here and
 *  neither is invented — the palette overlays what its source actually specifies. */
export interface PaletteAccents {
  primary: string;
  success: string;
  warning: string;
  error: string;
}

export const MASTER_PALETTE: Record<"dark" | "light", { surface: PaletteSurface; accents: PaletteAccents; label: string }> = {
  dark: {
    label: "母版建议 · 深色",
    surface: {
      bg: "#0B1018",
      sidebar: "#0E1520",
      panel: "#111C2B",
      panel2: "#17263A",
      border: "#2C3B50",
      ink: "#ECF2FA",
      muted: "#A4B2C6",
    },
    accents: { primary: "98 168 255", success: "105 213 181", warning: "255 200 120", error: "255 154 171" },
  },
  light: {
    label: "母版建议 · 浅色",
    // The pack gives sidebar and panel the SAME white and separates them with `line`; that is copied
    // verbatim rather than "improved", because a palette record that quietly differs from its source
    // is the drift this file exists to prevent.
    surface: {
      bg: "#F3F6FA",
      sidebar: "#FFFFFF",
      panel: "#FFFFFF",
      panel2: "#EAF0F7",
      border: "#CBD5E1",
      ink: "#172B46",
      muted: "#4F627A",
    },
    accents: { primary: "23 91 185", success: "20 107 83", warning: "135 83 9", error: "172 48 76" },
  },
};

export const PALETTE_LABELS: Record<PaletteId, string> = {
  worklab: "现行配色（默认）",
  master: "母版建议配色（20261009 包，可选）",
};

export function isPaletteId(value: string | null): value is PaletteId {
  return value === "worklab" || value === "master";
}
