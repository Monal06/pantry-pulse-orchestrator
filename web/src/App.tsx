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
      <List sx={{ px: 1 }}>
        {NAV_ITEMS.map((item, i) => {
          if ("divider" in item) return <Divider key={i} sx={{ my: 1 }} />;
          const isActive = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              component={NavLink}
              to={item.path}
              onClick={() => isMobile && setMobileOpen(false)}
              sx={{
                borderRadius: 2, mb: 0.5,
                bgcolor: isActive ? "primary.light" + "40" : "transparent",
                color: isActive ? "primary.dark" : "text.primary",
                "&:hover": { bgcolor: "primary.light" + "20" },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: isActive ? "primary.main" : "text.secondary" }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: isActive ? 700 : 500 }} />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
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
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            "& .MuiDrawer-paper": { width: DRAWER_WIDTH, borderRight: "1px solid #eee" },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {isMobile && (
          <AppBar position="sticky" color="inherit" elevation={1}>
            <Toolbar>
              <IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 1 }}>
                <MenuIcon />
              </IconButton>
              <FoodBank sx={{ color: "primary.main", mr: 1 }} />
              <Typography variant="h6" fontWeight={800} color="primary">FreshSave</Typography>
            </Toolbar>
          </AppBar>
        )}
        <Box sx={{ flex: 1, p: { xs: 2, sm: 3 }, maxWidth: 1000, width: "100%" }}>
          <Routes>
            <Route path="/" element={<InventoryPage />} />
            <Route path="/add-items" element={<AddItemsPage />} />
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
