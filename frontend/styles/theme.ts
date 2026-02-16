/**
 * Royal Sparkle Design Tokens
 * Central reference for the brand's design system.
 */

export const colors = {
  blush: "#F9E4E4",
  roseGold: "#B76E79",
  roseGoldLight: "#D4A0A7",
  roseGoldDark: "#8B4F57",
  beige: "#F5F0EB",
  cream: "#FFF8F0",
  dark: "#2D2D2D",
  white: "#FFFFFF",
} as const;

export const fonts = {
  heading: "'Playfair Display', serif",
  body: "'Poppins', sans-serif",
} as const;

export const shadows = {
  soft: "0 4px 20px rgba(183, 110, 121, 0.1)",
  hover: "0 8px 30px rgba(183, 110, 121, 0.2)",
} as const;

export const radii = {
  card: "16px",
  button: "9999px",
} as const;
