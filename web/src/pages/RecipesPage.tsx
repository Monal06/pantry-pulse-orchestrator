import { useEffect, useState, useCallback } from "react";
import {
  Box, Typography, Card, CardContent, Chip, IconButton, Snackbar,
  Alert, Stack, LinearProgress,
} from "@mui/material";
import { Favorite, FavoriteBorder, Delete } from "@mui/icons-material";
import { getFavoriteRecipes, toggleRecipeFavorite, deleteRecipe } from "../api";

export default function RecipesPage() {
  const [recipes, setRecipes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  const loadRecipes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFavoriteRecipes();
      setRecipes(data);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRecipes(); }, [loadRecipes]);

  const handleToggle = async (id: string) => {
    try {
      await toggleRecipeFavorite(id);
      await loadRecipes();
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteRecipe(id);
      setRecipes((prev) => prev.filter((r) => r.id !== id));
      setSnackbar("Recipe removed");
    } catch (e: any) {
      setSnackbar(e.message);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Saved Recipes</Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {recipes.length === 0 && !loading && (
        <Box sx={{ textAlign: "center", py: 8 }}>
          <Typography variant="h6" fontWeight={600} sx={{ mb: 1 }}>No saved recipes yet</Typography>
          <Typography color="text.secondary">
            Save recipes from meal suggestions by clicking the heart icon.
          </Typography>
        </Box>
      )}

      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2 }}>
        {recipes.map((recipe: any) => (
          <Card key={recipe.id}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                <Typography variant="h6" fontWeight={700} sx={{ flex: 1 }}>{recipe.name}</Typography>
                <Box>
                  <IconButton
                    size="small"
                    onClick={() => handleToggle(recipe.id)}
                    sx={{ color: recipe.is_favorite ? "#E53935" : "#9E9E9E" }}
                  >
                    {recipe.is_favorite ? <Favorite /> : <FavoriteBorder />}
                  </IconButton>
                  <IconButton size="small" onClick={() => handleDelete(recipe.id)}>
                    <Delete fontSize="small" />
                  </IconButton>
                </Box>
              </Stack>

              {recipe.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{recipe.description}</Typography>
              )}

              <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                <Chip label={`${recipe.prep_time_minutes}m`} size="small" />
                {recipe.times_cooked > 0 && (
                  <Chip label={`Cooked ${recipe.times_cooked}x`} size="small" />
                )}
              </Stack>

              {recipe.ingredients?.length > 0 && (
                <>
                  <Typography variant="subtitle2" fontWeight={700} sx={{ mt: 1 }}>Ingredients</Typography>
                  <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap sx={{ mb: 1 }}>
                    {recipe.ingredients.map((ing: string, i: number) => (
                      <Chip key={i} label={ing} size="small" sx={{ bgcolor: "#E8F5E9" }} />
                    ))}
                  </Stack>
                </>
              )}

              {recipe.instructions?.length > 0 && (
                <>
                  <Typography variant="subtitle2" fontWeight={700} sx={{ mt: 1 }}>Instructions</Typography>
                  {recipe.instructions.map((step: string, i: number) => (
                    <Typography key={i} variant="body2" color="text.secondary" sx={{ mb: 0.3 }}>
                      {i + 1}. {step}
                    </Typography>
                  ))}
                </>
              )}
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
