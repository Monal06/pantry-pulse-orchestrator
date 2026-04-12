import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: { main: "#16a34a", light: "#dcfce7", dark: "#15803d" },
    secondary: { main: "#f97316", light: "#ffedd5" },
    error: { main: "#ef4444", light: "#fee2e2" },
    background: { default: "#fcfcfc", paper: "#ffffff" },
    text: { primary: "#27272a", secondary: "#52525b" },
  },
  shape: { borderRadius: 24 },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h5: { fontWeight: 700, letterSpacing: "-0.02em" },
    h6: { fontWeight: 600, letterSpacing: "-0.01em" },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { fontWeight: 600, textTransform: "none" },
  },
  components: {
    MuiCard: {
      defaultProps: { elevation: 0, variant: "outlined" },
      styleOverrides: { 
        root: { 
          borderColor: "#e4e4e7",
          backgroundColor: "#ffffff",
          borderRadius: 24,
          boxShadow: "0 4px 24px rgba(0,0,0,0.02)",
          overflow: "hidden"
        } 
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { 
        root: { borderRadius: "24px", padding: "8px 24px" } 
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 12, fontWeight: 500 }
      }
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { borderBottom: "1px solid #e4e4e7", backgroundColor: "#ffffff" }
      }
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { borderRight: "1px solid #e4e4e7", backgroundColor: "#fcfcfc" }
      }
    }
  },
});

export const freshnessColor = (score: number): string => {
  if (score >= 70) return "#22c55e";
  if (score >= 50) return "#f59e0b";
  return "#ef4444";
};

export const freshnessLabel = (score: number): string => {
  if (score >= 70) return "Fresh";
  if (score >= 50) return "Use Soon";
  return "Critical";
};
