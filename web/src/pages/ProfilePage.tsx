import { useEffect, useState } from "react";
import {
  Box, Typography, Card, CardContent, Switch, Button, TextField,
  Chip, Snackbar, Alert, Stack,
  IconButton,
} from "@mui/material";
import { Add, Remove, Save } from "@mui/icons-material";
import { getDietaryProfile, updateDietaryProfile } from "../api";
import type { DietaryProfile } from "../api";

const TOGGLE_FIELDS: { key: keyof DietaryProfile; label: string; desc: string }[] = [
  { key: "vegetarian", label: "Vegetarian", desc: "No meat or fish" },
  { key: "vegan", label: "Vegan", desc: "No animal products" },
  { key: "gluten_free", label: "Gluten-Free", desc: "No wheat, barley, rye" },
  { key: "dairy_free", label: "Dairy-Free", desc: "No milk, cheese, butter" },
  { key: "nut_free", label: "Nut-Free", desc: "No tree nuts or peanuts" },
  { key: "halal", label: "Halal", desc: "Halal dietary laws" },
  { key: "kosher", label: "Kosher", desc: "Kosher dietary laws" },
  { key: "low_carb", label: "Low-Carb", desc: "Reduced carbohydrates" },
];

const CUISINES = [
  "Italian", "Mexican", "Chinese", "Japanese", "Indian", "Thai",
  "Mediterranean", "American", "Korean", "Middle Eastern", "French", "Vietnamese",
];

export default function ProfilePage() {
  const [profile, setProfile] = useState<DietaryProfile>({
    vegetarian: false, vegan: false, gluten_free: false, dairy_free: false,
    nut_free: false, halal: false, kosher: false, low_carb: false,
    allergies: [], dislikes: [], cuisine_preferences: [], household_size: 1,
  });
  const [allergyInput, setAllergyInput] = useState("");
  const [dislikeInput, setDislikeInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  useEffect(() => {
    getDietaryProfile().then(setProfile).catch(() => {});
  }, []);

  const toggleField = (key: keyof DietaryProfile) => {
    setProfile((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const addAllergy = () => {
    const val = allergyInput.trim();
    if (val && !profile.allergies.includes(val)) {
      setProfile((prev) => ({ ...prev, allergies: [...prev.allergies, val] }));
      setAllergyInput("");
    }
  };

  const addDislike = () => {
    const val = dislikeInput.trim();
    if (val && !profile.dislikes.includes(val)) {
      setProfile((prev) => ({ ...prev, dislikes: [...prev.dislikes, val] }));
      setDislikeInput("");
    }
  };

  const toggleCuisine = (c: string) => {
    setProfile((prev) => {
      const has = prev.cuisine_preferences.includes(c);
      return {
        ...prev,
        cuisine_preferences: has
          ? prev.cuisine_preferences.filter((x) => x !== c)
          : [...prev.cuisine_preferences, c],
      };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateDietaryProfile(profile);
      setSnackbar("Dietary preferences saved! Meal suggestions will respect these.");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Dietary Preferences</Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Dietary Restrictions</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Meal suggestions will strictly follow these restrictions.
          </Typography>
          {TOGGLE_FIELDS.map(({ key, label, desc }) => (
            <Box key={key} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", py: 1, borderBottom: "1px solid #eee" }}>
              <Box>
                <Typography fontWeight={600}>{label}</Typography>
                <Typography variant="body2" color="text.secondary">{desc}</Typography>
              </Box>
              <Switch checked={profile[key] as boolean} onChange={() => toggleField(key)} color="primary" />
            </Box>
          ))}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Allergies</Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
            <TextField
              label="Add allergy (e.g. shellfish)"
              value={allergyInput}
              onChange={(e) => setAllergyInput(e.target.value)}
              size="small"
              sx={{ flex: 1 }}
              onKeyDown={(e) => e.key === "Enter" && addAllergy()}
            />
            <Button variant="outlined" onClick={addAllergy} disabled={!allergyInput.trim()}>Add</Button>
          </Stack>
          <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
            {profile.allergies.map((a) => (
              <Chip key={a} label={a} onDelete={() => setProfile((p) => ({ ...p, allergies: p.allergies.filter((x) => x !== a) }))} sx={{ bgcolor: "#FFEBEE" }} />
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Foods You Dislike</Typography>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
            <TextField
              label="Add dislike (e.g. olives)"
              value={dislikeInput}
              onChange={(e) => setDislikeInput(e.target.value)}
              size="small"
              sx={{ flex: 1 }}
              onKeyDown={(e) => e.key === "Enter" && addDislike()}
            />
            <Button variant="outlined" onClick={addDislike} disabled={!dislikeInput.trim()}>Add</Button>
          </Stack>
          <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
            {profile.dislikes.map((d) => (
              <Chip key={d} label={d} onDelete={() => setProfile((p) => ({ ...p, dislikes: p.dislikes.filter((x) => x !== d) }))} sx={{ bgcolor: "#FFF3E0" }} />
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Favourite Cuisines</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Select cuisines you enjoy. Meal suggestions will lean towards these.
          </Typography>
          <Stack direction="row" flexWrap="wrap" spacing={0.5} useFlexGap>
            {CUISINES.map((c) => (
              <Chip
                key={c}
                label={c}
                onClick={() => toggleCuisine(c)}
                variant={profile.cuisine_preferences.includes(c) ? "filled" : "outlined"}
                color={profile.cuisine_preferences.includes(c) ? "primary" : "default"}
              />
            ))}
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Household Size</Typography>
          <Stack direction="row" alignItems="center" spacing={2}>
            <IconButton onClick={() => setProfile((p) => ({ ...p, household_size: Math.max(1, p.household_size - 1) }))}>
              <Remove />
            </IconButton>
            <Typography variant="h4" fontWeight={700}>{profile.household_size}</Typography>
            <IconButton onClick={() => setProfile((p) => ({ ...p, household_size: p.household_size + 1 }))}>
              <Add />
            </IconButton>
            <Typography color="text.secondary">
              {profile.household_size === 1 ? "person" : "people"}
            </Typography>
          </Stack>
        </CardContent>
      </Card>

      <Button
        variant="contained"
        startIcon={<Save />}
        onClick={handleSave}
        disabled={saving}
        size="large"
        fullWidth
      >
        Save Preferences
      </Button>

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="success" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
