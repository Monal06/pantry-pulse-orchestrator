import { useState } from "react";
import {
  Box, Typography, Card, CardContent, Tabs, Tab, Button, TextField,
  ToggleButtonGroup, ToggleButton, CircularProgress, Alert,
  Snackbar, Select, MenuItem, FormControl, InputLabel, Stack,
} from "@mui/material";
import {
  CameraAlt, Receipt, QrCodeScanner, Mic, Edit, CloudUpload,
} from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  analyzeFridgePhoto, analyzeReceipt, analyzeBarcode,
  addManualItem, analyzeVoiceInput, confirmReceiptItems,
} from "../api";

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
  const [receiptDate, setReceiptDate] = useState("");

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

  const handleReceiptUpload = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;
      setLoading(true);
      setResult(null);
      setReceiptDate("");
      try {
        const data = await analyzeReceipt(file);
        setResult(data);
        setReceiptDate(data.receipt_date || "");
      } catch (err: any) {
        setSnackbar(err.message);
      } finally {
        setLoading(false);
      }
    };
    input.click();
  };

  const handleConfirmReceiptItems = async () => {
    if (!result?.parsed_items?.length) return;
    setLoading(true);
    try {
      const finalDate = receiptDate || new Date().toISOString().split("T")[0];
      const added = await confirmReceiptItems(result.parsed_items, finalDate, "fridge");
      setResult({ ...result, items_added: added });
      setSnackbar(`${added.length} items added to your pantry`);
    } catch (e: any) {
      setSnackbar(e.message);
    } finally {
      setLoading(false);
    }
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
    if (!voiceText.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeVoiceInput(voiceText.trim());
      setResult(data);
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
              onClick={handleReceiptUpload}
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
            <Typography variant="h6" fontWeight={700} gutterBottom>Voice / Text Input</Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              Type or paste what you bought. For example: "I just bought milk, eggs, a bag of spinach, and two chicken breasts"
            </Typography>
            <TextField
              label="What did you buy?"
              value={voiceText}
              onChange={(e) => setVoiceText(e.target.value)}
              multiline
              rows={3}
              fullWidth
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              startIcon={<Mic />}
              onClick={handleVoiceSubmit}
              disabled={loading || !voiceText.trim()}
              size="large"
            >
              Parse and Add Items
            </Button>
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

            {/* Receipt confirmation step: items parsed but not yet added */}
            {tab === 1 && result.parsed_items?.length > 0 && !result.items_added?.length && (
              <Box sx={{ mb: 2 }}>
                <Typography sx={{ mb: 1 }}>
                  Found <strong>{result.parsed_items.length}</strong> item{result.parsed_items.length !== 1 ? "s" : ""}.
                  {result.store_name ? ` Store: ${result.store_name}.` : ""}
                </Typography>
                <Box sx={{ mb: 2, pl: 1 }}>
                  {result.parsed_items.map((item: any, i: number) => (
                    <Typography key={i} variant="body2" color="text.secondary">• {item.name} ({item.category})</Typography>
                  ))}
                </Box>
                <TextField
                  label="Purchase Date"
                  type="date"
                  value={receiptDate}
                  onChange={(e) => setReceiptDate(e.target.value)}
                  inputProps={{ max: new Date().toISOString().split("T")[0] }}
                  InputLabelProps={{ shrink: true }}
                  helperText={
                    result.receipt_date
                      ? `Date found on receipt: ${result.receipt_date}`
                      : "No date found on receipt — please enter it manually"
                  }
                  error={!receiptDate}
                  fullWidth
                  sx={{ mb: 2 }}
                />
                <Button
                  variant="contained"
                  onClick={handleConfirmReceiptItems}
                  disabled={!receiptDate || loading}
                  size="large"
                >
                  Add {result.parsed_items.length} items to Pantry
                </Button>
              </Box>
            )}

            {/* Normal result: items already added */}
            {result.items_added?.length > 0 && (
              <Typography>{result.items_added.length} items added to your pantry</Typography>
            )}
            {tab === 1 && result.parsed_items?.length === 0 && (
              <Typography color="text.secondary">No food items detected. Try a clearer photo.</Typography>
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
            {result.extraction_source && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {result.extraction_source === "fallback_heuristic" ? (
                  <>
                    <Typography component="span" variant="body2" color="warning.main" fontWeight={600}>
                      Extraction source: Fallback Parser
                    </Typography>
                    <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      (AI failed, used heuristic analysis)
                    </Typography>
                  </>
                ) : (
                  `Extraction source: ${result.extraction_source}`
                )}
              </Typography>
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
