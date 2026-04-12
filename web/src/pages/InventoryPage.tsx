import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Chip, IconButton, Button,
  ToggleButtonGroup, ToggleButton, LinearProgress, Snackbar, Alert,
  Tooltip, Stack,
} from "@mui/material";
import {
  Delete, Restaurant, AcUnit, Refresh,
  CameraAlt, Receipt, QrCodeScanner, Mic, Edit,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { getInventory, deleteItem, useItem, freezeItem } from "../api";
import { freshnessColor, freshnessLabel } from "../theme";

const ActionCard = ({ title, color, icon, onClick }: any) => (
  <Button
    onClick={onClick}
    sx={{
      bgcolor: color,
      borderRadius: "24px",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      width: { xs: "100%", sm: "160px" },
      height: "160px",
      textTransform: "none",
      color: "#0f172a",
      boxShadow: "none",
      "&:hover": { bgcolor: color, opacity: 0.9, boxShadow: "none" }
    }}
  >
    <Box sx={{ mb: 1, "& svg": { fontSize: 40 } }}>{icon}</Box>
    <Typography fontWeight={700} fontSize="0.95rem">{title}</Typography>
    <Typography variant="caption" color="text.secondary">Get Started</Typography>
  </Button>
);

type FilterType = "all" | "good" | "use_soon" | "critical";

export default function InventoryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getInventory();
      setItems(data);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadItems(); }, [loadItems]);

  const handleDelete = async (id: string) => {
    try {
      await deleteItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      setSnackbar("Item removed");
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const handleUse = async (id: string) => {
    try {
      await useItem(id, 1);
      await loadItems();
      setSnackbar("Item used");
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const handleFreeze = async (id: string) => {
    try {
      const result = await freezeItem(id);
      await loadItems();
      setSnackbar(result.message || "Item moved to freezer");
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    return item.freshness_status === filter;
  });

  const criticalCount = items.filter((i) => i.freshness_status === "critical").length;
  const useSoonCount = items.filter((i) => i.freshness_status === "use_soon").length;
  const freezableCount = items.filter(
    (i) => i.is_perishable && i.storage !== "freezer" && i.freshness_score < 70 && i.freshness_score >= 30
  ).length;

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: "-0.02em" }}>My Pantry</Typography>
        <Stack direction="row" spacing={1}>
          <IconButton onClick={loadItems} sx={{ border: "1px solid #cbd5e1", borderRadius: "12px", width: 44, height: 44 }}>
            <Refresh />
          </IconButton>
          <Button variant="contained" onClick={() => navigate("/add-items")} sx={{ bgcolor: "#111827", color: "white", borderRadius: "24px", px: 3, "&:hover": { bgcolor: "#000" } }}>
            + Add Items
          </Button>
        </Stack>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {(criticalCount > 0 || useSoonCount > 0 || freezableCount > 0) && (
        <Card sx={{ mb: 2, bgcolor: "#FFF8E1" }}>
          <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
            {criticalCount > 0 && (
              <Typography color="error" fontWeight={700} fontSize={13}>
                {criticalCount} item{criticalCount > 1 ? "s" : ""} need urgent attention
              </Typography>
            )}
            {useSoonCount > 0 && (
              <Typography sx={{ color: "#E65100", fontWeight: 600, fontSize: 13 }}>
                {useSoonCount} item{useSoonCount > 1 ? "s" : ""} should be used soon
              </Typography>
            )}
            {freezableCount > 0 && (
              <Typography sx={{ color: "#1565C0", fontWeight: 600, fontSize: 13 }}>
                {freezableCount} item{freezableCount > 1 ? "s" : ""} could be frozen to extend freshness
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      <Stack direction="row" spacing={1} sx={{ mb: 4, justifyContent: { xs: "flex-start", md: "flex-end" }, overflowX: "auto", pb: 1 }}>
        {[
          { id: "all", label: `All (${items.length})` },
          { id: "good", label: "Fresh" },
          { id: "use_soon", label: "Use Soon" },
          { id: "critical", label: "Critical" }
        ].map((f) => (
          <Chip 
            key={f.id}
            label={f.label}
            onClick={() => setFilter(f.id as FilterType)}
            sx={{ 
              borderRadius: "24px", px: 1, py: 2.5,
              bgcolor: filter === f.id ? "#e2e8f0" : "transparent",
              border: "1px solid #cbd5e1",
              fontWeight: 600,
              fontSize: "1rem",
              color: filter === f.id ? "#0f172a" : "#475569",
              "&:hover": { bgcolor: "#f1f5f9" }
            }}
          />
        ))}
      </Stack>

      {filtered.length === 0 && !loading && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Box sx={{ maxWidth: 400, mx: "auto", mb: 4, display: "flex", justifyContent: "center" }}>
            <img src="/assets/3d-pantry-placeholder.png" alt="pantry" style={{ maxWidth: "100%", borderRadius: "24px" }} />
          </Box>
          <Typography variant="h4" fontWeight={800} sx={{ mb: 6, letterSpacing: "-0.02em" }}>Your pantry is empty</Typography>
          
          <Stack direction="row" spacing={2} justifyContent="center" flexWrap="wrap" useFlexGap>
            <ActionCard title="Image Upload" color="#d1fae5" icon={<CameraAlt/>} onClick={() => navigate("/add-items?mode=fridge")} />
            <ActionCard title="Receipt Upload" color="#ccfbf1" icon={<Receipt/>} onClick={() => navigate("/add-items?mode=receipt")} />
            <ActionCard title="Barcode Scan" color="#ffedd5" icon={<QrCodeScanner/>} onClick={() => navigate("/add-items?mode=barcode")} />
            <ActionCard title="Voice Record" color="#ffe4e6" icon={<Mic/>} onClick={() => navigate("/add-items?mode=voice")} />
            <ActionCard title="Manual Entry" color="#f3e8ff" icon={<Edit/>} onClick={() => navigate("/add-items?mode=manual")} />
          </Stack>
        </Box>
      )}

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr", md: "1fr 1fr 1fr" }, gap: 2 }}>
        {filtered.map((item) => (
          <Card key={item.id} sx={{ borderLeft: `4px solid ${freshnessColor(item.freshness_score ?? 100)}` }}>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <Box>
                  <Typography fontWeight={700}>{item.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {item.quantity} {item.unit} &middot; {item.category} &middot; {item.storage}
                  </Typography>
                </Box>
                {item.is_perishable && (
                  <Box sx={{ textAlign: "right" }}>
                    <Typography fontWeight={800} sx={{ color: freshnessColor(item.freshness_score) }}>
                      {item.freshness_score}
                    </Typography>
                    <Chip
                      label={freshnessLabel(item.freshness_score)}
                      size="small"
                      sx={{ bgcolor: freshnessColor(item.freshness_score) + "20", fontWeight: 600 }}
                    />
                  </Box>
                )}
              </Box>
              {item.is_perishable && (
                <LinearProgress
                  variant="determinate"
                  value={item.freshness_score}
                  sx={{
                    mt: 1, height: 6, borderRadius: 3,
                    bgcolor: "#eee",
                    "& .MuiLinearProgress-bar": { bgcolor: freshnessColor(item.freshness_score) },
                  }}
                />
              )}
              <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 1, gap: 0.5 }}>
                <Tooltip title="Use 1">
                  <IconButton size="small" onClick={() => handleUse(item.id)} color="primary">
                    <Restaurant fontSize="small" />
                  </IconButton>
                </Tooltip>
                {item.is_perishable && item.storage !== "freezer" && item.freshness_score < 70 && (
                  <Tooltip title="Move to freezer">
                    <IconButton size="small" onClick={() => handleFreeze(item.id)} sx={{ color: "#1565C0" }}>
                      <AcUnit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
                <Tooltip title="Remove">
                  <IconButton size="small" onClick={() => handleDelete(item.id)} color="error">
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
