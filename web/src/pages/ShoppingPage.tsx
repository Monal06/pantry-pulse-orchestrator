import { useState } from "react";
import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  Snackbar, Alert, Checkbox, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Stack,
} from "@mui/material";
import { ShoppingCart } from "@mui/icons-material";
import { getShoppingList } from "../api";

const URGENCY_COLORS: Record<string, string> = {
  urgent: "#F44336",
  soon: "#FF9800",
  normal: "#4CAF50",
};

export default function ShoppingPage() {
  const [items, setItems] = useState<any[]>([]);
  const [basedOn, setBasedOn] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [snackbar, setSnackbar] = useState("");

  const loadList = async () => {
    setLoading(true);
    try {
      const data = await getShoppingList();
      setItems(data.shopping_list || []);
      setBasedOn(data.based_on || null);
      setMessage(data.message || "");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleChecked = (index: number) => {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Shopping List</Typography>

      <Button
        variant="contained"
        startIcon={<ShoppingCart />}
        onClick={loadList}
        disabled={loading}
        size="large"
        sx={{ mb: 3 }}
      >
        {items.length ? "Refresh List" : "Generate Shopping List"}
      </Button>

      {loading && !items.length && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <CircularProgress />
          <Typography color="text.secondary" sx={{ mt: 2 }}>Analyzing your usage patterns...</Typography>
        </Box>
      )}

      {message && !items.length && (
        <Card>
          <CardContent>
            <Typography color="text.secondary" textAlign="center">{message}</Typography>
          </CardContent>
        </Card>
      )}

      {basedOn && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
          <Chip label={`${basedOn.current_items} in pantry`} />
          <Chip label={`${basedOn.meals_cooked} meals cooked`} />
          <Chip label={`${basedOn.items_consumed} items used`} />
        </Stack>
      )}

      {items.filter((_, i) => !checked.has(i)).length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1 }}>
              To Buy ({items.filter((_, i) => !checked.has(i)).length})
            </Typography>
            <List dense disablePadding>
              {items.map((item, index) =>
                !checked.has(index) ? (
                  <ListItem
                    key={index}
                    disablePadding
                    secondaryAction={
                      <Chip
                        label={item.urgency}
                        size="small"
                        sx={{ bgcolor: (URGENCY_COLORS[item.urgency] || "#4CAF50") + "20" }}
                      />
                    }
                  >
                    <ListItemButton onClick={() => toggleChecked(index)} dense>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Checkbox edge="start" checked={false} />
                      </ListItemIcon>
                      <ListItemText primary={item.name} secondary={item.reason} />
                    </ListItemButton>
                  </ListItem>
                ) : null
              )}
            </List>
          </CardContent>
        </Card>
      )}

      {items.filter((_, i) => checked.has(i)).length > 0 && (
        <Card sx={{ bgcolor: "#F5F5F5" }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1, color: "text.secondary" }}>
              In Cart ({items.filter((_, i) => checked.has(i)).length})
            </Typography>
            <List dense disablePadding>
              {items.map((item, index) =>
                checked.has(index) ? (
                  <ListItem key={index} disablePadding>
                    <ListItemButton onClick={() => toggleChecked(index)} dense>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Checkbox edge="start" checked />
                      </ListItemIcon>
                      <ListItemText
                        primary={item.name}
                        sx={{ textDecoration: "line-through", color: "text.disabled" }}
                      />
                    </ListItemButton>
                  </ListItem>
                ) : null
              )}
            </List>
          </CardContent>
        </Card>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
