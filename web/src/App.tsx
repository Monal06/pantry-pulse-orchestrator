import { useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom";
import { ThemeProvider, CssBaseline } from "@mui/material";
import {
  Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText,
  AppBar, Toolbar, Typography, IconButton, useMediaQuery, Divider,
} from "@mui/material";
import {
  Kitchen, Restaurant, CalendarMonth, ShoppingCart, BarChart,
  People, Home, FoodBank, Favorite, Settings, Menu as MenuIcon,
  SpaOutlined,
} from "@mui/icons-material";
import { theme } from "./theme";

import InventoryPage from "./pages/InventoryPage";
import AddItemsPage from "./pages/AddItemsPage";
import ExitStrategyPage from "./pages/ExitStrategyPage";
import MealsPage from "./pages/MealsPage";
import WeeklyPlanPage from "./pages/WeeklyPlanPage";
import ShoppingPage from "./pages/ShoppingPage";
import DashboardPage from "./pages/DashboardPage";
import ProfilePage from "./pages/ProfilePage";
import CommunityPage from "./pages/CommunityPage";
import HouseholdPage from "./pages/HouseholdPage";
import RecipesPage from "./pages/RecipesPage";
import NutritionPage from "./pages/NutritionPage";

const DRAWER_WIDTH = 240;

const NAV_ITEMS = [
  { path: "/", label: "Pantry", icon: <Kitchen /> },
  { path: "/exit-strategy", label: "Give It a New Life", icon: <BarChart /> },
  { path: "/meals", label: "Meals", icon: <Restaurant /> },
  { path: "/weekly-plan", label: "Weekly Plan", icon: <CalendarMonth /> },
  { path: "/shopping", label: "Shopping", icon: <ShoppingCart /> },
  { path: "/dashboard", label: "Impact", icon: <BarChart /> },
  { divider: true },
  { path: "/recipes", label: "Saved Recipes", icon: <Favorite /> },
  { path: "/nutrition", label: "Nutrition", icon: <SpaOutlined /> },
  { path: "/community", label: "Community", icon: <People /> },
  { path: "/household", label: "Household", icon: <Home /> },
  { path: "/profile", label: "Diet Profile", icon: <Settings /> },
] as const;

function AppLayout() {
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

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
                "&:hover": { bgcolor: isActive ? "#bbf7d0" : "rgba(0,0,0,0.04)" },
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
            <Route path="/weekly-plan" element={<WeeklyPlanPage />} />
            <Route path="/shopping" element={<ShoppingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/community" element={<CommunityPage />} />
            <Route path="/household" element={<HouseholdPage />} />
            <Route path="/recipes" element={<RecipesPage />} />
            <Route path="/nutrition" element={<NutritionPage />} />
          </Routes>
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
