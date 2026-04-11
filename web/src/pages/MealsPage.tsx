import { useState, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Button, Chip, CircularProgress,
  Snackbar, Alert, Stack,
} from "@mui/material";
import { Restaurant, CalendarMonth, Favorite, FavoriteBorder, AutoAwesome, MonitorHeart } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { getMealSuggestions, recordCookedMeal, saveRecipe, generateMetabolicPlan, getInventory } from "../api";

class MealsStore {
  meals: any[] = [];
  loading = false;
  error = "";
  listeners: (() => void)[] = [];

  subscribe(listener: () => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach((l) => l());
  }

  async generate() {
    if (this.loading) return;
    this.loading = true;
    this.error = "";
    this.notify();

    try {
      const liveInventoryData = await getInventory();
      const realItems = liveInventoryData.map((item: any) => ({
        name: item.name,
        freshness_score: item.freshness_score || 100,
        category: item.category,
        visual_hazard: item.visual_hazard || false
      }));

      const payload = {
        inventory_items: realItems.length > 0 ? realItems : [
          { name: "Salmon", freshness_score: 15 },
          { name: "Spinach", freshness_score: 5 },
          { name: "Brown Rice", freshness_score: 90 }
        ],
        biometrics: {
          heart_rate_bpm: 85, hrv_ms: 30.5, sleep_score_100: 42,
          steps_today: 12000, readiness_score: 30, stress_level: "high"
        },
        profile: {
          vegetarian: false, vegan: false, gluten_free: false, dairy_free: false,
          nut_free: false, halal: false, kosher: false, low_carb: false,
          allergies: [], dislikes: [], cuisine_preferences: [], fitness_goals: ["endurance", "fat loss"], household_size: 1
        }
      };
      
      const res = await generateMetabolicPlan(payload);
      
      if (res.recipes && Array.isArray(res.recipes)) {
        this.meals = res.recipes.map((r: any) => ({
          name: r.name,
          description: r.description,
          metabolic_justification: r.justification,
          metabolic_score: r.metabolic_alignment_score,
          freshness_priority: "critical", 
          prep_time_minutes: r.prep_time_minutes,
          ingredients_used: r.ingredients_used,
          instructions: r.instructions
        }));
      } else {
        this.meals = [{
          name: res.name || "Unknown Recipe",
          description: res.description || "Failed to parse multiple recipes",
          metabolic_justification: res.justification || "Could not parse justification",
          metabolic_score: res.metabolic_alignment_score || 0,
          freshness_priority: "critical", 
          prep_time_minutes: res.prep_time_minutes || 30,
          ingredients_used: res.ingredients_used || [],
          instructions: res.instructions || []
        }];
      }
    } catch (e: any) {
      this.error = e.message;
    } finally {
      this.loading = false;
      this.notify();
    }
  }
}

const mealsStore = new MealsStore();

const PRIORITY_COLORS: Record<string, string> = {
  critical: "#F44336",
  use_soon: "#FF9800",
  normal: "#4CAF50",
};

const PRIORITY_LABELS: Record<string, string> = {
  critical: "Uses critical items",
  use_soon: "Uses items expiring soon",
  normal: "Regular recipe",
};

const FUN_LOADING_MESSAGES = [
  "Consulting the Metabolic Guard...",
  "Analyzing your biometric state...",
  "Matching freshness with flavor...",
  "Chopping virtual veggies...",
  "Simmering the data...",
  "Checking for critical ingredients...",
  "Sprinkling some AI magic...",
  "Optimizing for recovery...",
  "Waking up the digital chef...",
  "Reading your dietary profile...",
  "Tasting the code...",
  "Aligning macros and metrics...",
  "Rescuing items from the fridge...",
  "Plating your personalized plan...",
  "Calculating nutritional harmony..."
];

export default function MealsPage() {
  const navigate = useNavigate();
  const [meals, setMeals] = useState<any[]>(mealsStore.meals);
  const [loading, setLoading] = useState(mealsStore.loading);
  const [snackbar, setSnackbar] = useState("");
  const [tips, setTips] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loadingIndex, setLoadingIndex] = useState(0);
  
  useEffect(() => {
    return mealsStore.subscribe(() => {
      setMeals(mealsStore.meals);
      setLoading(mealsStore.loading);
      if (mealsStore.error) setSnackbar(`Generation failed: ${mealsStore.error}`);
    });
  }, []);

  useEffect(() => {
    let interval: any;
    if (loading) {
      interval = setInterval(() => {
        setLoadingIndex((prev) => (prev + 1) % FUN_LOADING_MESSAGES.length);
      }, 2000);
    } else {
      setLoadingIndex(0);
    }
    return () => clearInterval(interval);
  }, [loading]);

  const loadSuggestions = async () => {
    // Optionally randomize starting index
    setLoadingIndex(Math.floor(Math.random() * FUN_LOADING_MESSAGES.length));
    mealsStore.generate();
  };

  const handleSave = async (meal: any) => {
    try {
      await saveRecipe({
        name: meal.name,
        description: meal.description || "",
        ingredients: meal.ingredients_used || [],
        instructions: meal.instructions || [],
        prep_time_minutes: meal.prep_time_minutes || 30,
      });
      setSnackbar(`"${meal.name}" saved to your recipes!`);
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const handleCooked = async (meal: any) => {
    try {
      const result = await recordCookedMeal(meal.name, meal.ingredients_used);
      const deductedCount = result.deducted_from_inventory?.length ?? 0;
      setSnackbar(
        `"${meal.name}" cooked! ${deductedCount} ingredient${deductedCount !== 1 ? "s" : ""} deducted from pantry.`
      );
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Meal Suggestions</Typography>

      {summary && (
        <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mb: 2 }}>
          {summary.critical_items > 0 && (
            <Chip label={`${summary.critical_items} critical`} sx={{ bgcolor: "#FFEBEE" }} />
          )}
          {summary.use_soon_items > 0 && (
            <Chip label={`${summary.use_soon_items} use soon`} sx={{ bgcolor: "#FFF3E0" }} />
          )}
          <Chip label={`${summary.total_items} total items`} />
        </Stack>
      )}

      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <Button variant="outlined" startIcon={<CalendarMonth />} onClick={() => navigate("/weekly-plan")}>
          Weekly Plan
        </Button>
        <Button variant="outlined" startIcon={<Favorite />} onClick={() => navigate("/recipes")}>
          Saved Recipes
        </Button>
      </Stack>

      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<Restaurant />}
          onClick={loadSuggestions}
          disabled={loading}
          size="large"
        >
          {meals.length ? "Refresh Suggestions" : "Get Today's Meals"}
        </Button>
      </Stack>

      {loading && !meals.length && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <CircularProgress />
          <Typography color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
            {FUN_LOADING_MESSAGES[loadingIndex]}
          </Typography>
        </Box>
      )}

      {meals.map((meal, index) => (
        <Card
          key={index}
          sx={{
            mb: 2,
            borderLeft: `4px solid ${PRIORITY_COLORS[meal.freshness_priority] || "#4CAF50"}`,
          }}
        >
          <CardContent>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
              <Typography variant="h6" fontWeight={700}>{meal.name}</Typography>
              <Chip label={`${meal.prep_time_minutes} min`} size="small" icon={<Restaurant />} />
            </Box>

            <Typography color="text.secondary" sx={{ mb: 1 }}>{meal.description}</Typography>
            
            {meal.metabolic_justification && (
              <Box sx={{ mb: 2, p: 1.5, bgcolor: '#f0f7ff', borderRadius: 1, border: '1px solid #bbdefb' }}>
                <Stack direction="row" alignItems="center" gap={1} sx={{ mb: 0.5 }}>
                   <AutoAwesome color="primary" fontSize="small" />
                   <Typography variant="subtitle2" fontWeight={700} color="primary.main">
                     Metabolic Guard Active
                   </Typography>
                </Stack>
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  {meal.metabolic_justification}
                </Typography>
                {meal.metabolic_score && (
                  <Chip
                    icon={<MonitorHeart sx={{ fontSize: 16 }} />}
                    label={`Score: ${meal.metabolic_score}/100`}
                    color="success"
                    size="small"
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>
            )}

            <Chip
              label={PRIORITY_LABELS[meal.freshness_priority] || "Recipe"}
              size="small"
              sx={{
                bgcolor: (PRIORITY_COLORS[meal.freshness_priority] || "#4CAF50") + "20",
                mb: 2,
              }}
            />

            <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 0.5 }}>
              Ingredients from your pantry:
            </Typography>
            <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap sx={{ mb: 1 }}>
              {meal.ingredients_used?.map((ing: string, i: number) => (
                <Chip key={i} label={ing} size="small" sx={{ bgcolor: "#E8F5E9" }} />
              ))}
            </Stack>

            <Typography variant="subtitle2" fontWeight={700} sx={{ mt: 1, mb: 0.5 }}>Instructions:</Typography>
            {meal.instructions?.map((step: string, i: number) => (
              <Typography key={i} variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                {i + 1}. {step}
              </Typography>
            ))}

            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <Button variant="outlined" startIcon={<Restaurant />} onClick={() => handleCooked(meal)}>
                I Cooked This
              </Button>
              <Button variant="outlined" startIcon={<FavoriteBorder />} onClick={() => handleSave(meal)}>
                Save Recipe
              </Button>
            </Stack>
          </CardContent>
        </Card>
      ))}

      {tips.length > 0 && (
        <Card sx={{ bgcolor: "#FFF8E1" }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={700} sx={{ color: "#E65100", mb: 1 }}>
              Waste Prevention Tips
            </Typography>
            {tips.map((tip: any, i: number) => (
              <Box key={i} sx={{ mb: 1 }}>
                <Typography fontWeight={600}>{tip.item}:</Typography>
                <Typography variant="body2">{tip.tip}</Typography>
              </Box>
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
