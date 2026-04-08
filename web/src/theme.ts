import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: { main: "#2E7D32", light: "#A5D6A7", dark: "#1B5E20" },
    secondary: { main: "#F57F17", light: "#FFF9C4" },
    error: { main: "#C62828", light: "#FFCDD2" },
    background: { default: "#FAFAFA", paper: "#FFFFFF" },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: "'Inter', 'Roboto', 'Helvetica', 'Arial', sans-serif",
  },
  components: {
    MuiCard: {
      defaultProps: { elevation: 2 },
      styleOverrides: { root: { borderRadius: 12 } },
    },
    MuiButton: {
      styleOverrides: { root: { textTransform: "none", fontWeight: 600 } },
    },
  },
});

export const freshnessColor = (score: number): string => {
  if (score >= 70) return "#4CAF50";
  if (score >= 50) return "#FF9800";
  return "#F44336";
};

export const freshnessLabel = (score: number): string => {
  if (score >= 70) return "Fresh";
  if (score >= 50) return "Use Soon";
  return "Critical";
};
