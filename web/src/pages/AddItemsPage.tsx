import { useState } from "react";
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Button, TextField,
  ToggleButtonGroup, ToggleButton, CircularProgress, Alert,
  Snackbar, Select, MenuItem, FormControl, InputLabel, Stack,
  IconButton, Chip, keyframes,
} from "@mui/material";
import {
  CameraAlt, Receipt, QrCodeScanner, Mic, Edit, CloudUpload,
  Stop, DeleteOutline, Send,
} from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  analyzeFridgePhoto, analyzeReceipt, analyzeBarcode,
  addManualItem, analyzeVoiceInput,
} from "../api";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";

const pulseRing = keyframes`
  0%   { transform: scale(1);   opacity: 0.6; }
  70%  { transform: scale(1.8); opacity: 0; }
  100% { transform: scale(1.8); opacity: 0; }
`;

const CATEGORIES = [
  "dairy", "meat", "seafood", "fruit", "vegetable", "bread",
  "eggs", "condiment", "canned", "dry_goods", "beverage", "frozen", "other",
];

const TABS = [
  { label: "Fridge", icon: <CameraAlt /> },
  { label: "Receipt", icon: <Receipt /> },
  { label: "Barcode", icon: <QrCodeScanner /> },
  { label: "Voice", icon: <Mic /> },
  { label: "Manual", icon: <Edit /> },
];

export default function AddItemsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const modeMap: Record<string, number> = { fridge: 0, receipt: 1, barcode: 2, voice: 3, manual: 4 };
  const [tab, setTab] = useState(modeMap[searchParams.get("mode") || "manual"] ?? 4);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [snackbar, setSnackbar] = useState("");

  const [name, setName] = useState("");
  const [category, setCategory] = useState("other");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("item");
  const [storage, setStorage] = useState("fridge");
  const [isPerishable, setIsPerishable] = useState(true);
  const [barcodeInput, setBarcodeInput] = useState("");
  const [voiceText, setVoiceText] = useState("");
  const [purchaseDate, setPurchaseDate] = useState(
    new Date().toISOString().split('T')[0] // Today's date in YYYY-MM-DD format
  );

  // Voice recorder hook
  const voice = useVoiceRecorder();

  const handleFileUpload = async (analyzeFunc: (file: File) => Promise<any>) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setLoading(true);
      setResult(null);
      try {
        const data = await analyzeFunc(file);
        setResult(data);
      } catch (err: any) {
        setSnackbar(err.message);
      } finally {
        setLoading(false);
      }
    };
    input.click();
  };

  const handleBarcodeLookup = async () => {
    if (!barcodeInput.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeBarcode(barcodeInput.trim());
      setResult(data);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceSubmit = async () => {
    const text = (voice.transcript || voiceText).trim();
    if (!text) return;
    if (voice.isListening) voice.stopListening();
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeVoiceInput(text);
      setResult(data);
      voice.resetTranscript();
      setVoiceText("");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManualAdd = async () => {
    if (!name.trim()) {
      setSnackbar("Enter a name for the food item");
      return;
    }
    setLoading(true);
    try {
      await addManualItem({
        name: name.trim(),
        category,
        quantity: parseFloat(quantity) || 1,
        unit,
        storage,
        is_perishable: isPerishable,
        purchase_date: purchaseDate,
      });
      setSnackbar(`${name} added to your pantry`);
      navigate("/");
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={800} sx={{ mb: 2 }}>Add Items</Typography>

      <Tabs
        value={tab}
        onChange={(_, v) => { setTab(v); setResult(null); }}
        variant="scrollable"
        sx={{ mb: 3 }}
      >
        {TABS.map((t, i) => (
          <Tab key={i} icon={t.icon} label={t.label} iconPosition="start" />
        ))}
      </Tabs>

      {tab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Scan Fridge or Cupboard</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Upload a photo of your open fridge or cupboard. AI will identify food items and check for spoilage.
            </Typography>
            <Button
              variant="contained"
              startIcon={<CloudUpload />}
              onClick={() => handleFileUpload(analyzeFridgePhoto)}
              disabled={loading}
              size="large"
            >
              Upload Photo
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Scan Receipt</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Upload a photo of your grocery receipt. AI will extract food items and add them to your pantry.
            </Typography>
            <Button
              variant="contained"
              startIcon={<CloudUpload />}
              onClick={() => handleFileUpload(analyzeReceipt)}
              disabled={loading}
              size="large"
            >
              Upload Receipt Photo
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Barcode Lookup</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Enter a product barcode (EAN/UPC) to look it up in the Open Food Facts database.
            </Typography>
            <Stack direction="row" spacing={2} alignItems="flex-start">
              <TextField
                label="Barcode"
                value={barcodeInput}
                onChange={(e) => setBarcodeInput(e.target.value)}
                sx={{ flex: 1 }}
              />
              <Button
                variant="contained"
                onClick={handleBarcodeLookup}
                disabled={loading || !barcodeInput.trim()}
                size="large"
              >
                Look Up
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {tab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Voice Input</Typography>
            <Typography color="text.secondary" sx={{ mb: 3 }}>
              Tap the microphone and say what you bought, e.g. <em>"I got milk, eggs, a bag of spinach, and two chicken breasts."</em>
            </Typography>

            {/* ── Microphone button ── */}
            {voice.isSupported ? (
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", mb: 3 }}>
                <Box sx={{ position: "relative", display: "inline-flex" }}>
                  {/* Pulse ring when recording */}
                  {voice.isListening && (
                    <Box
                      sx={{
                        position: "absolute",
                        top: 0, left: 0, right: 0, bottom: 0,
                        borderRadius: "50%",
                        border: "3px solid",
                        borderColor: "error.main",
                        animation: `${pulseRing} 1.5s ease-out infinite`,
                      }}
                    />
                  )}
                  <IconButton
                    onClick={voice.isListening ? voice.stopListening : voice.startListening}
                    disabled={loading}
                    sx={{
                      width: 80,
                      height: 80,
                      bgcolor: voice.isListening ? "error.main" : "primary.main",
                      color: "#fff",
                      "&:hover": {
                        bgcolor: voice.isListening ? "error.dark" : "primary.dark",
                      },
                      transition: "all 0.3s ease",
                    }}
                  >
                    {voice.isListening ? <Stop sx={{ fontSize: 40 }} /> : <Mic sx={{ fontSize: 40 }} />}
                  </IconButton>
                </Box>

                <Typography
                  variant="body2"
                  sx={{
                    mt: 1.5,
                    fontWeight: 600,
                    color: voice.isListening ? "error.main" : "text.secondary",
                  }}
                >
                  {voice.isListening ? "Listening… tap to stop" : "Tap to start speaking"}
                </Typography>

                {voice.isListening && (
                  <Chip
                    label="● Recording"
                    size="small"
                    color="error"
                    sx={{
                      mt: 1,
                      fontWeight: 600,
                      "@keyframes blink": { "0%,100%": { opacity: 1 }, "50%": { opacity: 0.4 } },
                      animation: "blink 1s ease-in-out infinite",
                    }}
                  />
                )}
              </Box>
            ) : (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  Speech recognition is not supported in this browser. Please use <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong> for voice input, or type your items below.
                </Typography>
              </Alert>
            )}

            {/* ── Live transcript preview ── */}
            {voice.isListening && voice.interimTranscript && (
              <Box sx={{ mb: 2, p: 1.5, bgcolor: "#E8F5E9", borderRadius: 1, border: "1px dashed #A5D6A7" }}>
                <Typography variant="caption" fontWeight={600} color="primary.dark">
                  Hearing:
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: "italic", color: "text.secondary" }}>
                  {voice.interimTranscript}
                </Typography>
              </Box>
            )}

            {/* ── Error display ── */}
            {voice.error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => voice.resetTranscript()}>
                {voice.error}
              </Alert>
            )}

            {/* ── Editable transcript / text field ── */}
            <TextField
              label={voice.transcript ? "Edit transcript before submitting" : "Or type what you bought"}
              value={voice.transcript || voiceText}
              onChange={(e) => {
                if (voice.transcript) {
                  voice.setTranscript(e.target.value);
                } else {
                  setVoiceText(e.target.value);
                }
              }}
              multiline
              rows={3}
              fullWidth
              sx={{ mb: 2 }}
              placeholder="e.g. milk, eggs, a bag of spinach, and two chicken breasts"
            />

            {/* ── Action buttons ── */}
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                startIcon={<Send />}
                onClick={handleVoiceSubmit}
                disabled={loading || (!(voice.transcript || voiceText).trim())}
                size="large"
                sx={{ flex: 1 }}
              >
                Parse & Add Items
              </Button>
              {(voice.transcript || voiceText) && (
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteOutline />}
                  onClick={() => { voice.resetTranscript(); setVoiceText(""); }}
                  size="large"
                >
                  Clear
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}

      {tab === 4 && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Add Manually</Typography>
            <Stack spacing={2}>
              <TextField label="Item Name *" value={name} onChange={(e) => setName(e.target.value)} fullWidth />
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select value={category} label="Category" onChange={(e) => setCategory(e.target.value)}>
                  {CATEGORIES.map((c) => <MenuItem key={c} value={c}>{c}</MenuItem>)}
                </Select>
              </FormControl>
              <Stack direction="row" spacing={2}>
                <TextField label="Quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" sx={{ flex: 1 }} />
                <TextField label="Unit" value={unit} onChange={(e) => setUnit(e.target.value)} sx={{ flex: 1 }} />
              </Stack>
              <Box>
                <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>Storage Location</Typography>
                <ToggleButtonGroup value={storage} exclusive onChange={(_, v) => v && setStorage(v)} size="small">
                  <ToggleButton value="fridge">Fridge</ToggleButton>
                  <ToggleButton value="freezer">Freezer</ToggleButton>
                  <ToggleButton value="pantry">Pantry</ToggleButton>
                  <ToggleButton value="counter">Counter</ToggleButton>
                </ToggleButtonGroup>
              </Box>
              <Box>
                <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>Type</Typography>
                <ToggleButtonGroup value={isPerishable ? "perishable" : "non"} exclusive onChange={(_, v) => v && setIsPerishable(v === "perishable")} size="small">
                  <ToggleButton value="perishable">Perishable</ToggleButton>
                  <ToggleButton value="non">Non-Perishable</ToggleButton>
                </ToggleButtonGroup>
              </Box>
              <Box sx={{ pt: 1, border: "1px solid #e0e0e0", p: 2, borderRadius: 1, bgcolor: "#fafafa" }}>
                <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>📅 When was this purchased?</Typography>
                <TextField
                  type="date"
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                  fullWidth
                  size="small"
                  helperText="Defaults to today. Change if item is older."
                />
              </Box>
              <Button variant="contained" onClick={handleManualAdd} disabled={loading} size="large">
                Add to Pantry
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {loading && (
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 4 }}>
          <CircularProgress />
          <Typography color="text.secondary" sx={{ mt: 2 }}>Analyzing with AI...</Typography>
        </Box>
      )}

      {result && !loading && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight={700} gutterBottom>Analysis Complete</Typography>
            {result.items_added && (
              <Typography>{result.items_added.length} items added to your pantry</Typography>
            )}
            {result.item_added && (
              <Typography>Added: {result.item_added.name}</Typography>
            )}
            {result.spoilage_reports?.filter((r: any) => r.spoilage_detected).length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography fontWeight={700} color="error" gutterBottom>Spoilage Detected</Typography>
                {result.spoilage_reports
                  .filter((r: any) => r.spoilage_detected)
                  .map((report: any, i: number) => (
                    <Card key={i} sx={{ mb: 1, bgcolor: "#FFF3E0" }}>
                      <CardContent sx={{ py: 1.5, "&:last-child": { pb: 1.5 } }}>
                        <Typography fontWeight={600}>{report.item_name}</Typography>
                        {report.signs?.map((sign: string, j: number) => (
                          <Typography key={j} variant="body2" sx={{ color: "#BF360C", ml: 1 }}>• {sign}</Typography>
                        ))}
                        <Typography variant="body2" sx={{ fontStyle: "italic", mt: 0.5, color: "#4E342E" }}>
                          {report.recommendation}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
              </Box>
            )}
            {result.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>{result.description}</Typography>
            )}
            <Button variant="contained" onClick={() => navigate("/")} sx={{ mt: 2 }}>
              Back to Inventory
            </Button>
          </CardContent>
        </Card>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>
    </Box>
  );
}
