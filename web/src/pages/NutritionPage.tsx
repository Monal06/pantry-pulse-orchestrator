import { useState } from "react";
import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  Snackbar, Alert, LinearProgress, Stack,
} from "@mui/material";
import { getNutritionalBalance } from "../api";

const STATUS_COLORS: Record<string, string> = {
  good: "#4CAF50",
  moderate: "#FF9800",
  low: "#F44336",
};

const QUIRKY_TEXTS = [
  "Consulting the Broccoli Elders...",
  "Negotiating with your leftover pizza...",
  "Measuring the exact length of your celery stalks...",
  "Asking the fridge if it's happy...",
  "Calculating the velocity of an unswallowed vitamin...",
  "Convincing the kale it's delicious...",
  "Analyzing the nutritional value of your hopes and dreams...",
  "Indexing your snack drawer's dark matter...",
  "Scanning for sentient yogurt cultures...",
  "Checking if the apples are still looking fresh...",
  "Aggregating vitamins like Pokémon...",
  "Counting the fiber in your digital diet...",
  "Calibrating the 'Is it edible?' sensor...",
  "Summoning the spirits of forgotten groceries...",
];

function scoreColor(score: number): string {
  if (score >= 70) return "#4CAF50";
  if (score >= 40) return "#FF9800";
  return "#F44336";
}

export default function NutritionPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState(QUIRKY_TEXTS[0]);
  const [snackbar, setSnackbar] = useState("");

  const loadAnalysis = async () => {
    setLoading(true);
    setLoadingText(QUIRKY_TEXTS[Math.floor(Math.random() * QUIRKY_TEXTS.length)]);
    try {
      const result = await getNutritionalBalance();
      setData(result);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Nutrition Analysis</Typography>

      <Button
        variant="contained"
        onClick={loadAnalysis}
        disabled={loading}
        size="large"
        sx={{ mb: 3 }}
      >
        {data ? "Refresh Analysis" : "Analyze Nutritional Balance"}
      </Button>

      {loading && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <CircularProgress />
          <Typography
            color="text.secondary"
            sx={{ mt: 2, fontStyle: "italic" }}
          >
            {loadingText}
          </Typography>
        </Box>
      )}

      {data && !loading && (
        <>
          <Card sx={{ mb: 2, bgcolor: "#F1F8E9" }}>
            <CardContent sx={{ textAlign: "center" }}>
              <Typography variant="h2" fontWeight={800} sx={{ color: scoreColor(data.overall_score) }}>
                {data.overall_score}
              </Typography>
              <Typography color="text.secondary">Nutritional Balance Score</Typography>
              <LinearProgress
                variant="determinate"
                value={data.overall_score || 0}
                sx={{
                  height: 10, borderRadius: 5, my: 1.5,
                  bgcolor: "#eee",
                  "& .MuiLinearProgress-bar": { bgcolor: scoreColor(data.overall_score) },
                }}
              />
              <Typography>{data.overall_assessment}</Typography>
            </CardContent>
          </Card>

          {data.categories?.map((cat: any, i: number) => (
            <Card key={i} sx={{ mb: 1 }}>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
                  <Typography fontWeight={700}>{cat.name}</Typography>
                  <Chip
                    label={cat.status}
                    size="small"
                    sx={{ bgcolor: (STATUS_COLORS[cat.status] || "#9E9E9E") + "20" }}
                  />
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={cat.score || 0}
                  sx={{
                    height: 6, borderRadius: 3, mb: 0.5,
                    bgcolor: "#eee",
                    "& .MuiLinearProgress-bar": { bgcolor: STATUS_COLORS[cat.status] || "#9E9E9E" },
                  }}
                />
                <Typography variant="body2" color="text.secondary">{cat.detail}</Typography>
                {cat.suggestion && (
                  <Typography variant="body2" sx={{ color: "#1565C0", fontStyle: "italic", mt: 0.5 }}>
                    {cat.suggestion}
                  </Typography>
                )}
              </CardContent>
            </Card>
          ))}

          {data.missing_food_groups?.length > 0 && (
            <Card sx={{ mb: 2, bgcolor: "#FFF3E0" }}>
              <CardContent>
                <Typography fontWeight={700} sx={{ color: "#E65100", mb: 1 }}>Missing Food Groups</Typography>
                <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
                  {data.missing_food_groups.map((group: string, i: number) => (
                    <Chip key={i} label={group} size="small" sx={{ bgcolor: "#FFCC80" }} />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          )}

          {data.top_recommendations?.length > 0 && (
            <Card>
              <CardContent>
                <Typography fontWeight={700} sx={{ mb: 1 }}>Recommendations</Typography>
                {data.top_recommendations.map((rec: string, i: number) => (
                  <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>{i + 1}. {rec}</Typography>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
