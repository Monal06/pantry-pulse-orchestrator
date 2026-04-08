import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Chip, LinearProgress,
  Snackbar, Alert, Divider, Stack, Paper,
} from "@mui/material";
import { getWasteStats, getWasteEvents } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, e] = await Promise.all([getWasteStats(), getWasteEvents()]);
      setStats(s);
      setEvents(e);
    } catch (err: any) {
      setSnackbar(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const saveRate = stats?.save_rate_percent ?? 0;
  const hasData = stats && (stats.total_items_saved > 0 || stats.total_items_wasted > 0);

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Your Impact</Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Card sx={{ mb: 2, bgcolor: "#F1F8E9" }}>
        <CardContent>
          {hasData ? (
            <>
              <Stack direction="row" justifyContent="space-around" sx={{ mb: 2 }}>
                <StatBlock value={stats.total_items_saved} label="Items Saved" color="#4CAF50" />
                <StatBlock value={`$${stats.total_money_saved.toFixed(0)}`} label="Money Saved" color="#2E7D32" />
                <StatBlock value={`${stats.total_co2_saved_kg.toFixed(1)}kg`} label="CO2 Prevented" color="#1B5E20" />
              </Stack>
              <Divider sx={{ my: 1 }} />
              <Typography variant="subtitle2" fontWeight={700}>Save Rate: {saveRate.toFixed(0)}%</Typography>
              <LinearProgress
                variant="determinate"
                value={saveRate}
                sx={{
                  height: 10, borderRadius: 5, my: 1,
                  bgcolor: "#eee",
                  "& .MuiLinearProgress-bar": {
                    bgcolor: saveRate >= 70 ? "#4CAF50" : saveRate >= 40 ? "#FF9800" : "#F44336",
                  },
                }}
              />
              <Typography variant="body2" color="text.secondary">
                {saveRate >= 70
                  ? "Excellent! You're saving most of your food."
                  : saveRate >= 40
                    ? "Good progress. Try using items before they expire."
                    : "There's room to improve. Check meal suggestions daily!"}
              </Typography>
            </>
          ) : (
            <Typography color="text.secondary" textAlign="center" sx={{ py: 3 }}>
              Start tracking by using items in meals or logging waste. Your impact stats will appear here.
            </Typography>
          )}
        </CardContent>
      </Card>

      {hasData && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>Breakdown</Typography>
            <Stack direction="row" spacing={1}>
              <Paper sx={{ flex: 1, p: 2, textAlign: "center", bgcolor: "#E8F5E9", borderRadius: 2 }} elevation={0}>
                <Typography variant="h4" fontWeight={800}>{stats.total_items_saved}</Typography>
                <Typography variant="caption" color="text.secondary">Saved</Typography>
              </Paper>
              <Paper sx={{ flex: 1, p: 2, textAlign: "center", bgcolor: "#FFEBEE", borderRadius: 2 }} elevation={0}>
                <Typography variant="h4" fontWeight={800}>{stats.total_items_wasted}</Typography>
                <Typography variant="caption" color="text.secondary">Wasted</Typography>
              </Paper>
              <Paper sx={{ flex: 1, p: 2, textAlign: "center", bgcolor: "#E3F2FD", borderRadius: 2 }} elevation={0}>
                <Typography variant="h4" fontWeight={800}>{stats.total_items_frozen}</Typography>
                <Typography variant="caption" color="text.secondary">Frozen</Typography>
              </Paper>
            </Stack>
            {stats.total_money_wasted > 0 && (
              <Typography variant="body2" color="error" textAlign="center" sx={{ mt: 1.5 }}>
                ${stats.total_money_wasted.toFixed(2)} worth of food wasted
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {stats?.weekly_trend?.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>Weekly Trend</Typography>
            {stats.weekly_trend.map((week: any, i: number) => {
              return (
                <Stack key={i} direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Typography variant="caption" sx={{ width: 60, color: "text.secondary" }}>
                    {new Date(week.week_start).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </Typography>
                  <Box sx={{ flex: 1, display: "flex", height: 16, borderRadius: 2, overflow: "hidden", bgcolor: "#eee" }}>
                    {week.saved > 0 && (
                      <Box sx={{ flex: week.saved, bgcolor: "#4CAF50" }} />
                    )}
                    {week.wasted > 0 && (
                      <Box sx={{ flex: week.wasted, bgcolor: "#F44336" }} />
                    )}
                  </Box>
                  <Typography variant="caption" sx={{ width: 70, textAlign: "right", color: "text.secondary" }}>
                    {week.saved}S / {week.wasted}W
                  </Typography>
                </Stack>
              );
            })}
            <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 1 }}>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: "#4CAF50" }} />
                <Typography variant="caption">Saved</Typography>
              </Stack>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <Box sx={{ width: 10, height: 10, borderRadius: "50%", bgcolor: "#F44336" }} />
                <Typography variant="caption">Wasted</Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      )}

      {hasData && Object.keys(stats.category_breakdown || {}).length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>By Category</Typography>
            {Object.entries(stats.category_breakdown).map(([cat, data]: [string, any]) => (
              <Stack key={cat} direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
                <Chip label={cat} size="small" sx={{ minWidth: 80 }} />
                <Typography variant="body2" sx={{ color: "#4CAF50", fontWeight: 600 }}>{data.saved} saved</Typography>
                {data.wasted > 0 && (
                  <Typography variant="body2" color="error">{data.wasted} wasted</Typography>
                )}
                {data.value > 0 && (
                  <Typography variant="body2" sx={{ color: "#2E7D32", ml: "auto" }}>${data.value.toFixed(0)} saved</Typography>
                )}
              </Stack>
            ))}
          </CardContent>
        </Card>
      )}

      {events.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 1.5 }}>Recent Activity</Typography>
            {events.slice(-10).reverse().map((event: any, i: number) => (
              <Stack key={i} direction="row" alignItems="center" spacing={1.5} sx={{ py: 0.75 }}>
                <Typography sx={{ fontSize: 18, width: 24, textAlign: "center" }}>
                  {event.event_type === "saved" ? "✓" : event.event_type === "frozen" ? "❄" : event.event_type === "donated" ? "♥" : "✗"}
                </Typography>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="body2">{event.item_name}</Typography>
                  <Typography variant="caption" color="text.secondary">{event.event_type} · {event.date}</Typography>
                </Box>
                {event.estimated_value > 0 && (
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 600,
                      color: event.event_type === "wasted" ? "#F44336" : "#4CAF50",
                    }}
                  >
                    ${event.estimated_value.toFixed(2)}
                  </Typography>
                )}
              </Stack>
            ))}
          </CardContent>
        </Card>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}

function StatBlock({ value, label, color }: { value: string | number; label: string; color: string }) {
  return (
    <Box sx={{ textAlign: "center" }}>
      <Typography sx={{ fontSize: 28, fontWeight: 800, color }}>{value}</Typography>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
    </Box>
  );
}
