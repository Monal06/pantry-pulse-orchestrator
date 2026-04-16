import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box, Typography, Stack, Card, CardActionArea, CardContent,
  Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  LinearProgress, Snackbar, Alert, Divider, List, ListItem,
  ListItemText, ListItemIcon,
} from "@mui/material";
import { PlayArrow, Refresh, Inventory2, Close } from "@mui/icons-material";
import { addManualItem, deleteItem, getInventory } from "../api";
import { setDemoSafeModeEnabled } from "../utils/demoSafeMode";

// ─── helpers ────────────────────────────────────────────────────────────────

function offsetDate(daysAgo: number): string {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().split("T")[0];
}

const CATEGORY_EMOJI: Record<string, string> = {
  dairy: "🥛", meat: "🥩", seafood: "🐟", fruit: "🍎",
  vegetable: "🥦", bread: "🍞", eggs: "🥚", condiment: "🫙",
  canned: "🥫", dry_goods: "📦", beverage: "🧃", frozen: "🧊",
  other: "🍱",
};

// ─── types ───────────────────────────────────────────────────────────────────

interface DemoItemTemplate {
  name: string;
  category: string;
  quantity: number;
  unit: string;
  storage: string;
  is_perishable: boolean;
  daysAgo: number;
}

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  sceneEmojis: string[];
  gradient: string;
  accentColor: string;
  tags: string[];
  freshSummary: { fresh: number; soon: number; critical: number };
  items: DemoItemTemplate[];
}

// ─── pre-coded scenarios ─────────────────────────────────────────────────────

const SCENARIOS: DemoScenario[] = [
  {
    id: "family",
    title: "The Family Fridge",
    description:
      "A typical household fridge with dairy, proteins and veg at mixed freshness. Great for showing meal suggestions and freshness tracking.",
    sceneEmojis: ["🍎", "🥛", "🥚", "🧀", "🍗", "🥦"],
    gradient: "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 60%, #6ee7b7 100%)",
    accentColor: "#059669",
    tags: ["dairy", "meat", "mixed"],
    freshSummary: { fresh: 2, soon: 5, critical: 3 },
    items: [
      { name: "Free Range Eggs",  category: "eggs",      quantity: 6,   unit: "item",   storage: "fridge",  is_perishable: true,  daysAgo: 1  },
      { name: "Chicken Breast",   category: "meat",      quantity: 2,   unit: "item",   storage: "fridge",  is_perishable: true,  daysAgo: 2  },
      { name: "Broccoli",         category: "vegetable", quantity: 1,   unit: "head",   storage: "fridge",  is_perishable: true,  daysAgo: 3  },
      { name: "Apple",            category: "fruit",     quantity: 3,   unit: "item",   storage: "fridge",  is_perishable: true,  daysAgo: 2  },
      { name: "Orange Juice",     category: "beverage",  quantity: 1,   unit: "litre",  storage: "fridge",  is_perishable: true,  daysAgo: 5  },
      { name: "Carrots",          category: "vegetable", quantity: 4,   unit: "item",   storage: "fridge",  is_perishable: true,  daysAgo: 5  },
      { name: "Whole Milk",       category: "dairy",     quantity: 1,   unit: "litre",  storage: "fridge",  is_perishable: true,  daysAgo: 5  },
      { name: "Cheddar Cheese",   category: "dairy",     quantity: 200, unit: "g",      storage: "fridge",  is_perishable: true,  daysAgo: 6  },
      { name: "Butter",           category: "dairy",     quantity: 250, unit: "g",      storage: "fridge",  is_perishable: true,  daysAgo: 10 },
      { name: "Penne Pasta",      category: "dry_goods", quantity: 500, unit: "g",      storage: "pantry",  is_perishable: false, daysAgo: 30 },
    ],
  },
  {
    id: "market",
    title: "Farmer's Market Haul",
    description:
      "Just back from the market! All-fresh seasonal produce and artisan bread — everything at peak freshness. Perfect for meal planning.",
    sceneEmojis: ["🍓", "🥬", "🍅", "🥑", "🫐", "🥒"],
    gradient: "linear-gradient(135deg, #fef3c7 0%, #fde68a 60%, #fbbf24 100%)",
    accentColor: "#d97706",
    tags: ["fresh", "vegan", "produce"],
    freshSummary: { fresh: 10, soon: 0, critical: 0 },
    items: [
      { name: "Strawberries",  category: "fruit",     quantity: 250, unit: "g",     storage: "fridge",  is_perishable: true,  daysAgo: 0 },
      { name: "Kale",          category: "vegetable", quantity: 1,   unit: "bunch", storage: "fridge",  is_perishable: true,  daysAgo: 0 },
      { name: "Vine Tomatoes", category: "vegetable", quantity: 4,   unit: "item",  storage: "counter", is_perishable: true,  daysAgo: 0 },
      { name: "Avocado",       category: "fruit",     quantity: 2,   unit: "item",  storage: "counter", is_perishable: true,  daysAgo: 0 },
      { name: "Fresh Basil",   category: "vegetable", quantity: 1,   unit: "bunch", storage: "counter", is_perishable: true,  daysAgo: 0 },
      { name: "Courgette",     category: "vegetable", quantity: 2,   unit: "item",  storage: "fridge",  is_perishable: true,  daysAgo: 1 },
      { name: "Blueberries",   category: "fruit",     quantity: 150, unit: "g",     storage: "fridge",  is_perishable: true,  daysAgo: 0 },
      { name: "Sourdough",     category: "bread",     quantity: 1,   unit: "loaf",  storage: "pantry",  is_perishable: true,  daysAgo: 0 },
      { name: "Sweet Potato",  category: "vegetable", quantity: 3,   unit: "item",  storage: "pantry",  is_perishable: true,  daysAgo: 1 },
      { name: "Cucumber",      category: "vegetable", quantity: 1,   unit: "item",  storage: "fridge",  is_perishable: true,  daysAgo: 1 },
    ],
  },
  {
    id: "busy",
    title: "The Busy Week",
    description:
      "Mid-week reality check — salmon, wilting greens and leftovers that urgently need meal planning or an exit strategy.",
    sceneEmojis: ["🐟", "🥗", "🧀", "🍌", "⏱️", "🍋"],
    gradient: "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 60%, #93c5fd 100%)",
    accentColor: "#2563eb",
    tags: ["seafood", "dairy", "urgent"],
    freshSummary: { fresh: 2, soon: 3, critical: 5 },
    items: [
      { name: "Greek Yogurt",    category: "dairy",     quantity: 500, unit: "g",       storage: "fridge",  is_perishable: true,  daysAgo: 5  },
      { name: "Baby Spinach",    category: "vegetable", quantity: 200, unit: "g",       storage: "fridge",  is_perishable: true,  daysAgo: 4  },
      { name: "Salmon Fillet",   category: "seafood",   quantity: 2,   unit: "item",    storage: "fridge",  is_perishable: true,  daysAgo: 1  },
      { name: "Cherry Tomatoes", category: "vegetable", quantity: 200, unit: "g",       storage: "fridge",  is_perishable: true,  daysAgo: 6  },
      { name: "Hummus",          category: "condiment", quantity: 200, unit: "g",       storage: "fridge",  is_perishable: true,  daysAgo: 6  },
      { name: "Bananas",         category: "fruit",     quantity: 3,   unit: "item",    storage: "counter", is_perishable: true,  daysAgo: 4  },
      { name: "Canned Chickpeas",category: "canned",    quantity: 400, unit: "g",       storage: "pantry",  is_perishable: false, daysAgo: 60 },
      { name: "Lemon",           category: "fruit",     quantity: 2,   unit: "item",    storage: "fridge",  is_perishable: true,  daysAgo: 7  },
      { name: "Feta Cheese",     category: "dairy",     quantity: 200, unit: "g",       storage: "fridge",  is_perishable: true,  daysAgo: 8  },
      { name: "Leftover Rice",   category: "other",     quantity: 1,   unit: "portion", storage: "fridge",  is_perishable: true,  daysAgo: 3  },
    ],
  },
  {
    id: "critical",
    title: "Use It or Lose It!",
    description:
      "The fridge needs urgent attention — ideal for demoing the Exit Strategy and waste-prevention features. Almost everything is critical.",
    sceneEmojis: ["⚠️", "🥛", "🥬", "🥩", "🍞", "🚨"],
    gradient: "linear-gradient(135deg, #fee2e2 0%, #fecaca 60%, #fca5a5 100%)",
    accentColor: "#dc2626",
    tags: ["critical", "exit strategy"],
    freshSummary: { fresh: 0, soon: 2, critical: 6 },
    items: [
      { name: "Milk",             category: "dairy",     quantity: 1,   unit: "litre", storage: "fridge",  is_perishable: true, daysAgo: 9  },
      { name: "Lettuce",          category: "vegetable", quantity: 1,   unit: "head",  storage: "fridge",  is_perishable: true, daysAgo: 8  },
      { name: "Overripe Bananas", category: "fruit",     quantity: 4,   unit: "item",  storage: "counter", is_perishable: true, daysAgo: 7  },
      { name: "Yogurt",           category: "dairy",     quantity: 200, unit: "g",     storage: "fridge",  is_perishable: true, daysAgo: 7  },
      { name: "Ground Beef",      category: "meat",      quantity: 300, unit: "g",     storage: "fridge",  is_perishable: true, daysAgo: 4  },
      { name: "Stale Bread",      category: "bread",     quantity: 1,   unit: "loaf",  storage: "pantry",  is_perishable: true, daysAgo: 6  },
      { name: "Apple",            category: "fruit",     quantity: 2,   unit: "item",  storage: "fridge",  is_perishable: true, daysAgo: 5  },
      { name: "Cheddar Cheese",   category: "dairy",     quantity: 150, unit: "g",     storage: "fridge",  is_perishable: true, daysAgo: 12 },
    ],
  },
];

// ─── component ───────────────────────────────────────────────────────────────

export default function DemoPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<DemoScenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    msg: string;
    severity: "success" | "error" | "info";
  }>({ msg: "", severity: "success" });

  useEffect(() => {
    // Demo page always opts into AI-free mode for presentation reliability.
    setDemoSafeModeEnabled(true);
  }, []);

  const clearPantry = useCallback(async () => {
    const existing = await getInventory();
    await Promise.all(existing.map((item: any) => deleteItem(item.id)));
    return existing.length as number;
  }, []);

  const handleLoad = useCallback(
    async (clearFirst: boolean) => {
      if (!selected) return;
      setLoading(true);
      try {
        if (clearFirst) await clearPantry();

        const items = selected.items.map((t) => ({
          name: t.name,
          category: t.category,
          quantity: t.quantity,
          unit: t.unit,
          storage: t.storage,
          is_perishable: t.is_perishable,
          purchase_date: offsetDate(t.daysAgo),
        }));

        await Promise.all(items.map((item) => addManualItem(item)));

        // Ensure demo-safe behavior remains active after loading a scenario.
        setDemoSafeModeEnabled(true);

        const label = selected.title;
        setSelected(null);
        setSnackbar({
          msg: `"${label}" loaded — ${items.length} items added. Demo safe mode is ON.`,
          severity: "success",
        });
        setTimeout(() => navigate("/"), 1400);
      } catch (err: any) {
        setSnackbar({ msg: err.message, severity: "error" });
      } finally {
        setLoading(false);
      }
    },
    [selected, clearPantry, navigate],
  );

  const handleReset = useCallback(async () => {
    setResetting(true);
    try {
      const n = await clearPantry();
      setSnackbar({ msg: `Pantry cleared — ${n} item${n === 1 ? "" : "s"} removed`, severity: "info" });
    } catch (err: any) {
      setSnackbar({ msg: err.message, severity: "error" });
    } finally {
      setResetting(false);
    }
  }, [clearPantry]);

  const closeSnackbar = () => setSnackbar((s) => ({ ...s, msg: "" }));

  return (
    <Box>
      {/* ── header ── */}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={1.5}
        sx={{ mb: 1 }}
      >
        <Box>
          <Stack direction="row" alignItems="center" spacing={1.5} flexWrap="wrap">
            <Typography variant="h5" fontWeight={800}>
              Demo Pantry Loader
            </Typography>
            <Chip
              label="⚡ No AI credits used"
              size="small"
              sx={{ bgcolor: "#dcfce7", color: "#15803d", fontWeight: 700 }}
            />
          </Stack>
          <Typography color="text.secondary" sx={{ mt: 0.5, fontSize: "0.95rem" }}>
            Pick a fridge scenario to instantly populate the pantry with pre-coded items.
          </Typography>
        </Box>

        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleReset}
          disabled={resetting || loading}
          color="error"
          sx={{ flexShrink: 0, borderRadius: "12px" }}
        >
          {resetting ? "Clearing…" : "Reset Pantry"}
        </Button>
      </Stack>

      <Divider sx={{ mb: 3 }} />

      {/* ── scenario grid ── */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
          gap: 2.5,
        }}
      >
        {SCENARIOS.map((scenario) => (
          <Card
            key={scenario.id}
            elevation={0}
            sx={{
              border: "2px solid #f1f5f9",
              borderRadius: "20px",
              overflow: "hidden",
              transition: "all 0.2s ease",
              "&:hover": {
                border: `2px solid ${scenario.accentColor}`,
                transform: "translateY(-3px)",
                boxShadow: `0 8px 24px ${scenario.accentColor}22`,
              },
            }}
          >
            <CardActionArea onClick={() => setSelected(scenario)} disabled={loading || resetting}>
              {/* ── scene visual ── */}
              <Box
                sx={{
                  background: scenario.gradient,
                  height: 156,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                    gap: 1.5,
                  }}
                >
                  {scenario.sceneEmojis.map((emoji, i) => (
                    <Box
                      key={i}
                      sx={{
                        width: 54,
                        height: 54,
                        borderRadius: "14px",
                        bgcolor: "rgba(255,255,255,0.65)",
                        backdropFilter: "blur(6px)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 28,
                        boxShadow: "0 2px 8px rgba(0,0,0,0.07)",
                      }}
                    >
                      {emoji}
                    </Box>
                  ))}
                </Box>
              </Box>

              {/* ── card body ── */}
              <CardContent sx={{ px: 2.5, pt: 2, pb: 2.5 }}>
                <Typography variant="h6" fontWeight={800} sx={{ mb: 0.5 }}>
                  {scenario.title}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 1.5, lineHeight: 1.6 }}
                >
                  {scenario.description}
                </Typography>

                {/* freshness summary */}
                <Stack direction="row" spacing={0.75} flexWrap="wrap" sx={{ mb: 1.5, rowGap: 0.75 }}>
                  {scenario.freshSummary.fresh > 0 && (
                    <Chip
                      label={`${scenario.freshSummary.fresh} fresh`}
                      size="small"
                      sx={{ bgcolor: "#dcfce7", color: "#16a34a", fontWeight: 700, fontSize: "0.72rem" }}
                    />
                  )}
                  {scenario.freshSummary.soon > 0 && (
                    <Chip
                      label={`${scenario.freshSummary.soon} use soon`}
                      size="small"
                      sx={{ bgcolor: "#fef3c7", color: "#d97706", fontWeight: 700, fontSize: "0.72rem" }}
                    />
                  )}
                  {scenario.freshSummary.critical > 0 && (
                    <Chip
                      label={`${scenario.freshSummary.critical} critical`}
                      size="small"
                      sx={{ bgcolor: "#fee2e2", color: "#dc2626", fontWeight: 700, fontSize: "0.72rem" }}
                    />
                  )}
                </Stack>

                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Stack direction="row" spacing={0.5} flexWrap="wrap">
                    {scenario.tags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: "0.68rem", height: 22, color: "text.secondary", borderColor: "#e2e8f0" }}
                      />
                    ))}
                  </Stack>
                  <Typography
                    variant="caption"
                    fontWeight={800}
                    sx={{ color: scenario.accentColor, whiteSpace: "nowrap" }}
                  >
                    {scenario.items.length} items →
                  </Typography>
                </Stack>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>

      {/* ── detail / confirm dialog ── */}
      <Dialog
        open={!!selected}
        onClose={() => !loading && setSelected(null)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: "20px" } }}
      >
        {selected && (
          <>
            <DialogTitle sx={{ pb: 0.5 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" alignItems="center" spacing={1.5}>
                  <Typography variant="h6" fontWeight={800}>
                    {selected.title}
                  </Typography>
                  <Chip
                    label={`${selected.items.length} items`}
                    size="small"
                    sx={{ bgcolor: "#f1f5f9", fontWeight: 600 }}
                  />
                </Stack>
                <Button
                  onClick={() => setSelected(null)}
                  disabled={loading}
                  size="small"
                  sx={{ minWidth: 0, color: "text.secondary" }}
                >
                  <Close fontSize="small" />
                </Button>
              </Stack>
            </DialogTitle>

            <DialogContent sx={{ pt: 1 }}>
              {loading && (
                <LinearProgress sx={{ mb: 2, borderRadius: 4 }} />
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selected.description}
              </Typography>

              <List dense disablePadding>
                {selected.items.map((item, i) => (
                  <ListItem key={i} disablePadding sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 34, fontSize: 18 }}>
                      {CATEGORY_EMOJI[item.category] ?? "🍱"}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography variant="body2" fontWeight={600}>
                          {item.name}
                        </Typography>
                      }
                      secondary={`${item.quantity} ${item.unit} · ${item.storage} · ${
                        item.daysAgo === 0 ? "bought today" : `${item.daysAgo}d ago`
                      }`}
                    />
                  </ListItem>
                ))}
              </List>
            </DialogContent>

            <DialogActions sx={{ px: 3, pb: 3, gap: 1, flexDirection: { xs: "column", sm: "row" } }}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => handleLoad(false)}
                disabled={loading}
                startIcon={<Inventory2 />}
                sx={{ borderRadius: "12px" }}
              >
                Add to Existing Pantry
              </Button>
              <Button
                variant="contained"
                fullWidth
                onClick={() => handleLoad(true)}
                disabled={loading}
                startIcon={loading ? undefined : <PlayArrow />}
                sx={{
                  borderRadius: "12px",
                  bgcolor: selected.accentColor,
                  "&:hover": { bgcolor: selected.accentColor, filter: "brightness(0.88)" },
                }}
              >
                {loading ? "Loading items…" : "Replace & Load Pantry"}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* ── snackbar ── */}
      <Snackbar
        open={!!snackbar.msg}
        autoHideDuration={3500}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={snackbar.severity} onClose={closeSnackbar} sx={{ borderRadius: "12px" }}>
          {snackbar.msg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
