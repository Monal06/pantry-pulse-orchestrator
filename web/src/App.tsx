import { useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, useMediaQuery, Divider, Chip,
} from "@mui/material";
import {
  Kitchen, Restaurant, BarChart, FoodBank, Favorite, Settings, Menu as MenuIcon,
  SpaOutlined,
} from "@mui/icons-material";
import { theme } from "./theme";

import InventoryPage from "./pages/InventoryPage";
import AddItemsPage from "./pages/AddItemsPage";
import ExitStrategyPage from "./pages/ExitStrategyPage";
import MealsPage from "./pages/MealsPage";
import DashboardPage from "./pages/DashboardPage";
import ProfilePage from "./pages/ProfilePage";
import RecipesPage from "./pages/RecipesPage";
import NutritionPage from "./pages/NutritionPage";
import DemoPage from "./pages/DemoPage";
import { isDemoSafeModeEnabled, isPresentationLockEnabled, setDemoSafeModeEnabled, setPresentationLockEnabled } from "./utils/demoSafeMode";

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
  { path: "/", label: "Pantry", icon: <Kitchen /> },
  { path: "/exit-strategy", label: "Give It a New Life", icon: <BarChart /> },
  { path: "/meals", label: "Meals", icon: <Restaurant /> },
  { divider: true },
  { path: "/dashboard", label: "Impact", icon: <BarChart /> },
  { path: "/recipes", label: "Saved Recipes", icon: <Favorite /> },
  { path: "/nutrition", label: "Nutrition", icon: <SpaOutlined /> },
  { path: "/profile", label: "Diet Profile", icon: <Settings /> },
] as const;

const DEMO_BANNER_PATHS = new Set([
  "/",
  "/exit-strategy",
  "/meals",
  "/dashboard",
  "/recipes",
  "/nutrition",
  "/profile",
]);

function AppLayout() {
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const presentationLocked = isPresentationLockEnabled();
  const demoSafeMode = isDemoSafeModeEnabled();
  const showDemoBanner = demoSafeMode && DEMO_BANNER_PATHS.has(location.pathname);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const lockRequested = params.get("demo") === "1" || params.get("lock") === "1";
    if (lockRequested) {
      setPresentationLockEnabled(true);
      setDemoSafeModeEnabled(true);
      if (location.pathname !== "/demo") {
        navigate("/demo", { replace: true });
      }
      return;
    }

    if (isPresentationLockEnabled()) {
      // Persist AI-free behavior for the entire locked presentation session.
      setDemoSafeModeEnabled(true);
    }
  }, [location.pathname, location.search, navigate]);

  const drawerContent = (
    <Box>
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 1 }}>
        <FoodBank sx={{ color: "primary.main", fontSize: 32 }} />
        <Typography variant="h6" fontWeight={800} color="primary">
          FreshSave
        </Typography>
      </Box>
      <Divider />
      <List sx={{ px: 1, py: 2 }}>
        {NAV_ITEMS.map((item, i) => {
          if ("divider" in item) return <Divider key={i} sx={{ my: 1, opacity: 0.5 }} />;
          const isActive = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              component={NavLink}
              to={item.path}
              onClick={() => isMobile && setMobileOpen(false)}
              sx={{
                borderRadius: "16px", mb: 0.5, mx: 1,
                  bgcolor: isActive ? "#bbf7d0" : "transparent",
                  color: isActive ? "#065f46" : "#475569",
                  border: "1px solid transparent",
                "&:hover": {
                    bgcolor: isActive ? "#bbf7d0" : "rgba(0,0,0,0.04)",
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: "inherit" }}>
                {item.icon}
              </ListItemIcon>
                <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: isActive ? 700 : 500, fontSize: "0.95rem" }} />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ 
      display: "flex", minHeight: "100vh", p: { xs: 0, md: 2 }, gap: { xs: 0, md: 2 },
      background: "radial-gradient(at 0% 0%, #fef3c7 0px, transparent 50%), radial-gradient(at 100% 0%, #d1fae5 0px, transparent 50%), radial-gradient(at 100% 100%, #cffafe 0px, transparent 50%), radial-gradient(at 0% 100%, #fee2e2 0px, transparent 50%), #f8fafc"
    }}>
      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{ "& .MuiDrawer-paper": { width: DRAWER_WIDTH } }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Box
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            bgcolor: "rgba(255, 255, 255, 0.4)",
            backdropFilter: "blur(20px)",
            borderRadius: "24px",
            display: { xs: "none", md: "flex" },
            flexDirection: "column",
            overflow: "hidden",
            boxShadow: "0 4px 24px rgba(0,0,0,0.02)"
          }}
        >
          {drawerContent}
        </Box>
      )}

      <Box sx={{ 
        flex: 1, display: "flex", flexDirection: "column",
        bgcolor: "#ffffff", borderRadius: { xs: 0, md: "24px" },
        boxShadow: "0 4px 24px rgba(0,0,0,0.02)",
        overflow: "hidden"
      }}>
        {isMobile && (
          <AppBar position="sticky" color="inherit">
            <Toolbar>
              <IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 1 }}>
                <MenuIcon />
              </IconButton>
              <FoodBank sx={{ color: "primary.main", mr: 1 }} />
              <Typography variant="h6" fontWeight={800} color="primary">FreshSave</Typography>
            </Toolbar>
          </AppBar>
        )}
        <Box sx={{ flex: 1, p: { xs: 2, sm: 4 }, width: "100%", overflowY: "auto" }}>
          <Routes>
            <Route path="/" element={<InventoryPage />} />
            <Route path="/add-items" element={<AddItemsPage />} />
            <Route path="/exit-strategy" element={<ExitStrategyPage />} />
            <Route path="/meals" element={<MealsPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/recipes" element={<RecipesPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
            <Route path="/demo" element={<DemoPage />} />
          </Routes>

          {showDemoBanner && (
            <Box sx={{ mt: 3, display: "flex", justifyContent: "center" }}>
              <Chip
                size="small"
                label="Demo safe mode: local strategy engine"
                sx={{ bgcolor: "#dcfce7", color: "#166534", fontWeight: 700 }}
              />
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ThemeProvider>
  );
}
