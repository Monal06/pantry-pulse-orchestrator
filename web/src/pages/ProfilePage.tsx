import { useEffect, useState, useRef } from "react";
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

  // Live wearable mock state
  const [liveHr, setLiveHr] = useState(85);
  const [liveSteps, setLiveSteps] = useState(12040);

  useEffect(() => {
    getDietaryProfile().then(setProfile).catch(() => {});

    // Wearable data simulation
    const hrInterval = setInterval(() => {
      setLiveHr((prev) => {
        const jump = Math.random() > 0.5 ? 1 : -1;
        return Math.min(Math.max(prev + jump, 75), 95);
      });
    }, 1500);

    const stepsInterval = setInterval(() => {
      if (Math.random() > 0.5) {
         setLiveSteps((prev) => prev + Math.floor(Math.random() * 3) + 1);
      }
    }, 2000);
    
    return () => {
      clearInterval(hrInterval);
      clearInterval(stepsInterval);
    };
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

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={700} gutterBottom>Core Biometrics</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Your baseline details used for metabolic calculations.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField label="Age" type="number" size="small" defaultValue={28} />
            <TextField label="Weight (kg)" type="number" size="small" defaultValue={70} />
            <TextField label="Height (cm)" type="number" size="small" defaultValue={175} />
          </Stack>
        </CardContent>
      </Card>

      <Card sx={{ mb: 4, background: 'linear-gradient(to right, #f8f9fa, #e9ecef)' }}>
        <CardContent>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
            <Typography variant="h6" fontWeight={700}>🟢 Apple Watch / Oura Synced</Typography>
            <Chip color="success" size="small" label="Live Data" />
          </Stack>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            These biometrics are streaming from your wearable device and are dynamically piped into the Metabolic Guard.
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <Typography variant="subtitle2" color="text.secondary">Resting HR</Typography>
              <Typography variant="h5" fontWeight={700} color="error.main">{liveHr} bpm</Typography>
              <Typography variant="caption" color="text.secondary">Elevated (+10)</Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <Typography variant="subtitle2" color="text.secondary">Sleep Score</Typography>
              <Typography variant="h5" fontWeight={700} color="warning.main">42/100</Typography>
              <Typography variant="caption" color="text.secondary">Poor Recovery</Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <Typography variant="subtitle2" color="text.secondary">Readiness</Typography>
              <Typography variant="h5" fontWeight={700} color="error.main">30/100</Typography>
              <Typography variant="caption" color="error">High Stress Detected</Typography>
            </Box>
            <Box sx={{ p: 2, bgcolor: 'white', borderRadius: 1, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <Typography variant="subtitle2" color="text.secondary">Steps Today</Typography>
              <Typography variant="h5" fontWeight={700} color="primary.main">{liveSteps.toLocaleString()}</Typography>
              <Typography variant="caption" color="primary">Goal Met!</Typography>
            </Box>
          </Box>
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
