import { useState } from "react";
import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  Snackbar, Alert, Divider, Stack,
} from "@mui/material";
import { CalendarMonth } from "@mui/icons-material";
import { getWeeklyMealPlan } from "../api";

export default function WeeklyPlanPage() {
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  const loadPlan = async () => {
    setLoading(true);
    try {
      const data = await getWeeklyMealPlan();
      setPlan(data);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Weekly Meal Plan</Typography>

      <Button
        variant="contained"
        startIcon={<CalendarMonth />}
        onClick={loadPlan}
        disabled={loading}
        size="large"
        sx={{ mb: 3 }}
      >
        {plan ? "Regenerate Weekly Plan" : "Generate 7-Day Meal Plan"}
      </Button>

      {loading && !plan && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <CircularProgress />
          <Typography color="text.secondary" sx={{ mt: 2 }}>Planning your week...</Typography>
        </Box>
      )}

      {plan?.summary && (
        <Card sx={{ mb: 2, bgcolor: "#F1F8E9" }}>
          <CardContent>
            <Typography>{plan.summary}</Typography>
            {plan.shopping_needed?.length > 0 && (
              <Box sx={{ mt: 1.5 }}>
                <Typography variant="subtitle2" fontWeight={700}>Shopping needed:</Typography>
                <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap sx={{ mt: 0.5 }}>
                  {plan.shopping_needed.map((item: string, i: number) => (
                    <Chip key={i} label={item} size="small" />
                  ))}
                </Stack>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {plan?.days?.map((day: any) => (
        <Card key={day.day} sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" fontWeight={800} color="primary" gutterBottom>
              {day.date_label}
            </Typography>

            {day.items_to_use_today?.length > 0 && (
              <Box sx={{ mb: 2, p: 1.5, bgcolor: "#FFF3E0", borderRadius: 2 }}>
                <Typography variant="body2" fontWeight={700} sx={{ color: "#E65100", mb: 0.5 }}>
                  Must use today:
                </Typography>
                <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
                  {day.items_to_use_today.map((item: string, i: number) => (
                    <Chip key={i} label={item} size="small" sx={{ bgcolor: "#FFCC80" }} />
                  ))}
                </Stack>
              </Box>
            )}

            {["breakfast", "lunch", "dinner"].map((mealType) => {
              const meal = day.meals?.[mealType];
              if (!meal) return null;
              return (
                <Box key={mealType} sx={{ mb: 1.5 }}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Typography
                      variant="caption"
                      fontWeight={700}
                      sx={{ textTransform: "uppercase", color: "text.secondary" }}
                    >
                      {mealType}
                    </Typography>
                    {meal.prep_time_minutes && (
                      <Typography variant="caption" color="text.disabled">
                        {meal.prep_time_minutes}m
                      </Typography>
                    )}
                  </Stack>
                  <Typography fontWeight={600} sx={{ my: 0.5 }}>{meal.name}</Typography>
                  <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
                    {meal.ingredients_used?.map((ing: string, i: number) => (
                      <Chip key={i} label={ing} size="small" sx={{ bgcolor: "#E8F5E9" }} />
                    ))}
                  </Stack>
                  <Divider sx={{ mt: 1.5 }} />
                </Box>
              );
            })}
          </CardContent>
        </Card>
      ))}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
