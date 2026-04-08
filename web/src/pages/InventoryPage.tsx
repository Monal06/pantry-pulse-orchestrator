import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Chip, IconButton, Button,
  ToggleButtonGroup, ToggleButton, LinearProgress, Snackbar, Alert,
  Tooltip, Stack,
} from "@mui/material";
import {
  Delete, Restaurant, AcUnit, Refresh,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { getInventory, deleteItem, useItem, freezeItem } from "../api";
import { freshnessColor, freshnessLabel } from "../theme";

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
        <Typography variant="h5" fontWeight={800}>My Pantry</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<Refresh />} onClick={loadItems}>Refresh</Button>
          <Button variant="contained" onClick={() => navigate("/add-items")}>+ Add Items</Button>
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

      <ToggleButtonGroup
        value={filter}
        exclusive
        onChange={(_, v) => v && setFilter(v)}
        size="small"
        sx={{ mb: 2 }}
      >
        <ToggleButton value="all">All ({items.length})</ToggleButton>
        <ToggleButton value="good">Fresh</ToggleButton>
        <ToggleButton value="use_soon">Use Soon</ToggleButton>
        <ToggleButton value="critical">Critical</ToggleButton>
      </ToggleButtonGroup>

      {filtered.length === 0 && !loading && (
        <Box sx={{ textAlign: "center", py: 8 }}>
          <Typography variant="h3" sx={{ mb: 1 }}>🥗</Typography>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>Your pantry is empty</Typography>
          <Typography color="text.secondary">
            Click "+ Add Items" to add items by photo, receipt, barcode, voice, or manually
          </Typography>
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
