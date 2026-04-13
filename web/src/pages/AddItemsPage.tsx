import { useState, useRef, useCallback, useEffect } from "react";
import {
  Box, Typography, Card, CardContent, Button, TextField,
  ToggleButtonGroup, ToggleButton, CircularProgress, Alert,
  Snackbar, Select, MenuItem, FormControl, InputLabel, Stack,
  IconButton, Chip, keyframes, Dialog, DialogContent,
  DialogTitle,
} from "@mui/material";
import {
  CameraAlt, Receipt, Mic, Edit, CloudUpload,
  Stop, DeleteOutline, Send, Camera, Close,
} from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  analyzeFridgePhoto, analyzeReceipt,
  addManualItem, analyzeVoiceInput, confirmReceiptItems,
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
  { label: "Photo", icon: <CameraAlt /> },
  { label: "Receipt", icon: <Receipt /> },
  { label: "Voice", icon: <Mic /> },
  { label: "Manual", icon: <Edit /> },
];

const FUN_ANALYSIS_MESSAGES = [
  "Squinting at your fridge contents...",
  "Counting the carrot sticks...",
  "Is that a leftover pizza I see?",
  "Scanning for sentient broccoli...",
  "Reading the fine print on that digital receipt...",
  "Consulting the Freshness Oracle...",
  "Calculating the half-life of your spinach...",
  "Matching items with our food database...",
  "Checking if the yogurt has started a revolution...",
  "Decrypting receipt hieroglyphics...",
  "Sniffing out the best-before dates...",
  "Wait, was that a dragon fruit or just a cool rock?",
  "Analyzing the crispiness factor...",
  "Organizing your digital pantry shelves...",
  "Asking the AI if an apple a day still works...",
  "Verifying that your lettuce isn't planning an escape...",
  "Converting calories into cold hard data...",
  "Checking if those eggs are still feeling sunny...",
  "Bargaining with the bananas for one more day...",
  "Telling the milk to keep it cool...",
  "Searching for the lost island of Tupperware lids...",
  "Wait—did that cucumber just wink at me?",
  "Investigating the suspicious moisture in the vegetable drawer...",
  "Cross-referencing your diet with your bank account...",
  "AI is currently debating the difference between a fruit and a berry...",
  "Calculating how many smoothies this spinach can survive...",
  "Checking if the cheese has developed its own personality...",
  "Analyzing the existential dread of that single grape...",
  "Asking the fridge why the light really goes out...",
  "Scanning for hidden chocolate stashes...",
  "Trying to remember if tomatoes belong in the fridge (they don't!)...",
  "Checking if your kale is organic or just pretentious...",
  "Listening to the sizzle in your imagination...",
  "Plotting the ultimate leftover resurrection...",
  "Applying quantum physics to your grocery bill...",
  "Determining if that's a condiment or a science project...",
  "Checking with the butter to see if it's feeling smooth...",
  "Consulting the ghost of Julia Child...",
  "Scanning for secret ingredients—mostly love and salt...",
  "Wait, I think I found a forgotten lime in the back...",
  "Attempting to translate 'Product of Earth'...",
  "Ensuring your avocados don't ripen all at once (good luck!)...",
  "Mapping the snack-zone topology...",
  "Wrestling with the wrapper of mystery leftovers...",
  "AI is wondering why humans love sourdough so much...",
  "Cataloging your collection of half-empty pickle jars..."
];

export default function AddItemsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const modeMap: Record<string, number> = { photo: 0, fridge: 0, receipt: 1, voice: 2, manual: 3 };
  const modeParam = searchParams.get("mode");
  const isDirectMode = !!modeParam;
  const [tab, setTab] = useState(modeMap[modeParam || "manual"] ?? 3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [snackbar, setSnackbar] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loadingIndex, setLoadingIndex] = useState(0);

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
  const [receiptDate, setReceiptDate] = useState("");

  // Voice recorder hook
  const voice = useVoiceRecorder();

  // Camera state
  const [cameraOpen, setCameraOpen] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraLoading, setCameraLoading] = useState(false);
  const [cameraMode, setCameraMode] = useState<'photo' | 'receipt'>('photo');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const handleFileUpload = async (analyzeFunc: (file: File) => Promise<any>) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/*";
    input.onchange = async (e: any) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // Generate image preview
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);

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

  // Camera functions
  const startCamera = useCallback(async (mode: 'photo' | 'receipt' = 'photo') => {
    setCameraLoading(true);
    setCameraMode(mode);
    try {
      console.log('Requesting camera access for:', mode);
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: true // Simplified constraints first
      });
      console.log('Camera stream obtained:', mediaStream);
      console.log('Video tracks:', mediaStream.getVideoTracks());
      
      setStream(mediaStream);
      setCameraOpen(true);
    } catch (error: any) {
      console.error('Error accessing camera:', error);
      setSnackbar(`Unable to access camera: ${error.message}`);
    } finally {
      setCameraLoading(false);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setCameraOpen(false);
  }, [stream]);

  const capturePhoto = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    // Set canvas dimensions to video dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Generate preview from canvas
    const previewDataUrl = canvas.toDataURL('image/jpeg', 0.8);
    setImagePreview(previewDataUrl);
    
    // Convert canvas to blob
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      
      setLoading(true);
      setResult(null);
      stopCamera();
      
      try {
        // Create a File from the blob
        const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
        const data = await analyzeFridgePhoto(file);
        setResult(data);
      } catch (err: any) {
        setSnackbar(err.message);
      } finally {
        setLoading(false);
      }
    }, 'image/jpeg', 0.8);
  }, [stopCamera]);

  const captureReceipt = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    // Set canvas dimensions to video dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Generate preview from canvas
    const previewDataUrl = canvas.toDataURL('image/jpeg', 0.8);
    setImagePreview(previewDataUrl);
    
    // Convert canvas to blob
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      
      setLoading(true);
      setResult(null);
      stopCamera();
      
      try {
        // Create a File from the blob
        const file = new File([blob], 'receipt-capture.jpg', { type: 'image/jpeg' });
        const data = await analyzeReceipt(file);
        setResult(data);
      } catch (err: any) {
        setSnackbar(err.message);
      } finally {
        setLoading(false);
      }
    }, 'image/jpeg', 0.8);
  }, [stopCamera]);

  // Effect to handle video stream setup
  useEffect(() => {
    console.log('useEffect triggered:', { cameraOpen, stream: !!stream, videoRef: !!videoRef.current });
    
    if (cameraOpen && stream && videoRef.current) {
      console.log('Setting up video stream...', stream);
      const video = videoRef.current;
      
      video.srcObject = stream;
      
      // Add event listeners to debug video loading
      video.onloadedmetadata = () => {
        console.log('Video metadata loaded');
        video.play().then(() => {
          console.log('Video playing successfully');
        }).catch((error) => {
          console.error('Error playing video:', error);
        });
      };
      
      video.onerror = (error) => {
        console.error('Video error:', error);
      };
      
      video.oncanplay = () => {
        console.log('Video can play');
      };
    }
  }, [cameraOpen, stream]);

  useEffect(() => {
    let interval: any;
    if (loading) {
      setLoadingIndex(Math.floor(Math.random() * FUN_ANALYSIS_MESSAGES.length));
      interval = setInterval(() => {
        setLoadingIndex((prev) => (prev + 1) % FUN_ANALYSIS_MESSAGES.length);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [loading]);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4" fontWeight={800} sx={{ letterSpacing: "-0.02em" }}>Add Items</Typography>
        {isDirectMode && (
          <Button variant="outlined" onClick={() => navigate("/")} sx={{ borderColor: "#cbd5e1", color: "#475569" }}>
            Back
          </Button>
        )}
      </Box>

      {!isDirectMode && (
        <Stack direction="row" spacing={1} sx={{ mb: 4, overflowX: "auto", pb: 1 }}>
          {TABS.map((t, i) => (
            <Chip
              key={i}
              label={t.label}
              icon={t.icon}
              onClick={() => { setTab(i); setResult(null); setImagePreview(null); }}
              sx={{
                borderRadius: "24px", px: 1, py: 2.5,
                bgcolor: tab === i ? "#0f172a" : "transparent",
                color: tab === i ? "#ffffff" : "#475569",
                border: tab === i ? "1px solid #0f172a" : "1px solid #cbd5e1",
                fontWeight: 600,
                fontSize: "1rem",
                "& .MuiChip-icon": { color: tab === i ? "#ffffff" : "inherit" },
                "&:hover": { bgcolor: tab === i ? "#1e293b" : "#f1f5f9" }
              }}
            />
          ))}
        </Stack>
      )}

      {tab === 0 && (
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" fontWeight={800} gutterBottom sx={{ letterSpacing: "-0.01em" }}>Photo Analysis</Typography>
            <Typography color="text.secondary" sx={{ mb: 4, fontSize: "1.1rem" }}>
              Take a photo or upload an image of your fridge, cupboard, or food items. AI will identify items and check for spoilage.
            </Typography>
            
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                variant="contained"
                startIcon={<Camera />}
                onClick={() => startCamera('photo')}
                disabled={loading || cameraLoading}
                size="large"
                sx={{ flex: 1 }}
              >
                {cameraLoading ? "Starting Camera..." : "Take Photo"}
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<CloudUpload />}
                onClick={() => handleFileUpload(analyzeFridgePhoto)}
                disabled={loading}
                size="large"
                sx={{ flex: 1 }}
              >
                Upload Photo
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" fontWeight={800} gutterBottom sx={{ letterSpacing: "-0.01em" }}>Receipt Scanner</Typography>
            <Typography color="text.secondary" sx={{ mb: 4, fontSize: "1.1rem" }}>
              Take a photo or upload an image of your grocery receipt. AI will extract food items and add them to your pantry.
            </Typography>
            
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                variant="contained"
                startIcon={<Camera />}
                onClick={() => startCamera('receipt')}
                disabled={loading || cameraLoading}
                size="large"
                sx={{ flex: 1 }}
              >
                {cameraLoading ? "Starting Camera..." : "Scan Receipt"}
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<CloudUpload />}
                onClick={handleReceiptUpload}
                disabled={loading}
                size="large"
                sx={{ flex: 1 }}
              >
                Upload Receipt
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}



      {tab === 2 && (
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" fontWeight={800} gutterBottom sx={{ letterSpacing: "-0.01em" }}>Voice Input</Typography>
            <Typography color="text.secondary" sx={{ mb: 4, fontSize: "1.1rem" }}>
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

      {tab === 3 && (
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h5" fontWeight={800} gutterBottom sx={{ letterSpacing: "-0.01em" }}>Add Manually</Typography>
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
        <Card sx={{ mt: 3, overflow: "hidden" }}>
          <CardContent>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={3} alignItems="center">
              {/* Image preview thumbnail */}
              {imagePreview && (
                <Box
                  sx={{
                    width: { xs: "100%", sm: 180 },
                    minWidth: 180,
                    height: 180,
                    borderRadius: 2,
                    overflow: "hidden",
                    border: "2px solid",
                    borderColor: "primary.light",
                    flexShrink: 0,
                    position: "relative",
                  }}
                >
                  <img
                    src={imagePreview}
                    alt="Uploaded preview"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                  {/* Scanning animation overlay */}
                  <Box
                    sx={{
                      position: "absolute",
                      top: 0, left: 0, right: 0, bottom: 0,
                      background: "linear-gradient(180deg, transparent 0%, rgba(25,118,210,0.15) 50%, transparent 100%)",
                      backgroundSize: "100% 200%",
                      animation: "scanLine 2s ease-in-out infinite",
                      "@keyframes scanLine": {
                        "0%": { backgroundPosition: "0% -100%" },
                        "100%": { backgroundPosition: "0% 200%" },
                      },
                    }}
                  />
                </Box>
              )}

              {/* Analysis status */}
              <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 1, py: 2 }}>
                <CircularProgress size={48} />
                <Typography fontWeight={700} color="primary" sx={{ mt: 2, textAlign: "center" }}>
                  {FUN_ANALYSIS_MESSAGES[loadingIndex]}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, textAlign: "center" }}>
                  Identifying items and checking freshness
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {result && !loading && (
        <Card sx={{ mt: 3, overflow: "hidden" }}>
          <CardContent>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={3} alignItems="flex-start">
              {/* Image preview thumbnail in results */}
              {imagePreview && (
                <Box
                  sx={{
                    width: { xs: "100%", sm: 160 },
                    minWidth: 160,
                    height: 160,
                    borderRadius: 2,
                    overflow: "hidden",
                    border: "1px solid #e0e0e0",
                    flexShrink: 0,
                  }}
                >
                  <img
                    src={imagePreview}
                    alt="Analyzed image"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                </Box>
              )}

              {/* Results content */}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="h6" fontWeight={700} gutterBottom>Analysis Complete ✅</Typography>
                {result.parsed_items?.length === 0 && !(result.items_added?.length > 0) && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>
                      ⚠️ No items found on the receipt
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1.5, color: "text.secondary" }}>
                      The receipt parser couldn't extract any food items. This often happens when:
                    </Typography>
                    <ul style={{ margin: "0.5rem 0", paddingLeft: "1.5rem" }}>
                      <li><Typography variant="body2">Receipt is blurry or poorly lit</Typography></li>
                      <li><Typography variant="body2">Text is too small or faded</Typography></li>
                      <li><Typography variant="body2">Receipt is at an angle or partially cut off</Typography></li>
                      <li><Typography variant="body2">Image is a photograph of a printed receipt (try scanning instead)</Typography></li>
                    </ul>
                    <Typography variant="body2" sx={{ mt: 1.5, mb: 1 }}>Try these tips:</Typography>
                    <ul style={{ margin: "0.5rem 0", paddingLeft: "1.5rem" }}>
                      <li><Typography variant="body2">Use better lighting (natural sunlight or bright lamp)</Typography></li>
                      <li><Typography variant="body2">Place receipt flat on a surface</Typography></li>
                      <li><Typography variant="body2">Get closer so text is larger and sharper</Typography></li>
                      <li><Typography variant="body2">Clean the camera lens</Typography></li>
                      <li><Typography variant="body2">Try uploading a different photo of the same receipt</Typography></li>
                    </ul>
                    <Button 
                      variant="outlined" 
                      onClick={() => { setResult(null); setImagePreview(null); }} 
                      sx={{ mt: 2 }}
                      size="small"
                    >
                      Try Another Photo
                    </Button>
                  </Alert>
                )}
                {result.parsed_items?.length > 0 && !(result.items_added?.length > 0) && (
                  <Box sx={{ mb: 2 }}>
                    <Typography sx={{ mb: 1 }}>{result.parsed_items.length} items found on receipt</Typography>
                    {receiptDate ? (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        Receipt date: {receiptDate}
                      </Typography>
                    ) : (
                      <Box sx={{ pt: 1, border: "1px solid #e0e0e0", p: 2, borderRadius: 1, bgcolor: "#fafafa", mb: 1.5 }}>
                        <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>📅 When was this purchased?</Typography>
                        <TextField
                          type="date"
                          value={receiptDate}
                          onChange={(e) => setReceiptDate(e.target.value)}
                          fullWidth
                          size="small"
                          helperText="Date not found on receipt. Defaults to today if left blank."
                          inputProps={{ max: new Date().toISOString().split("T")[0] }}
                        />
                      </Box>
                    )}
                    <Button variant="contained" onClick={handleConfirmReceiptItems} disabled={loading} sx={{ mt: 1 }}>
                      Add {result.parsed_items.length} Items to Pantry
                    </Button>
                  </Box>
                )}
                {result.items_added?.length > 0 && (
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
                <Button variant="contained" onClick={() => { navigate("/"); setImagePreview(null); }} sx={{ mt: 2 }}>
                  Back to Inventory
                </Button>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")}>
        <Alert severity="info" onClose={() => setSnackbar("")}>{snackbar}</Alert>
      </Snackbar>

      {/* Hidden canvas for photo capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* ── Camera dialog ── */}
      <Dialog 
        open={cameraOpen} 
        onClose={stopCamera} 
        fullWidth 
        maxWidth="sm"
        TransitionProps={{
          onEntered: () => {
            // Try to set the stream when dialog fully opens
            if (cameraOpen && stream && videoRef.current) {
              console.log('Dialog opened, setting video stream...');
              videoRef.current.srcObject = stream;
              videoRef.current.play().catch(console.error);
            }
          }
        }}
      >
        <DialogTitle>
          {cameraMode === 'receipt' ? 'Scan Receipt' : 'Scan with Camera'}
        </DialogTitle>
        <DialogContent sx={{ display: "flex", flexDirection: "column", alignItems: "center", p: 3 }}>
          <Typography color="text.secondary" sx={{ mb: 2, textAlign: "center" }}>
            {cameraMode === 'receipt' 
              ? 'Position the receipt within the frame and ensure all text is clearly visible. Tap the shutter button to capture.'
              : 'Align the item within the frame and ensure good lighting. Tap the shutter button to capture a photo.'
            }
          </Typography>

          {/* Debug info */}
          {stream && (
            <Typography variant="caption" sx={{ mb: 1, color: "green" }}>
              Stream active: {stream.getVideoTracks().length} video track(s)
            </Typography>
          )}

          {/* Video stream from camera */}
          <Box sx={{ position: "relative", width: "100%", maxWidth: 400, aspectRatio: "4/3", bgcolor: "#000", borderRadius: 2 }}>
            {!stream && (
              <Box
                sx={{
                  position: "absolute",
                  top: 0, left: 0, width: "100%", height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "white",
                  flexDirection: "column",
                  gap: 2,
                }}
              >
                <CircularProgress color="inherit" />
                <Typography variant="body2">Initializing camera...</Typography>
              </Box>
            )}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              controls={false}
              width="100%"
              height="100%"
              style={{
                position: "absolute",
                top: 0, left: 0, width: "100%", height: "100%",
                objectFit: "cover",
                borderRadius: 8,
                backgroundColor: "#000",
              }}
            />

            {/* Shutter button */}
            <IconButton
              onClick={cameraMode === 'receipt' ? captureReceipt : capturePhoto}
              sx={{
                position: "absolute",
                bottom: 16,
                left: "50%",
                transform: "translateX(-50%)",
                bgcolor: "primary.main",
                color: "#fff",
                width: 56,
                height: 56,
                borderRadius: "50%",
                boxShadow: 2,
                "&:hover": {
                  bgcolor: "primary.dark",
                },
                transition: "all 0.3s ease",
              }}
            >
              <Camera sx={{ fontSize: 28 }} />
            </IconButton>

            {/* Camera mode indicator */}
            <Box
              sx={{
                position: "absolute",
                top: 8,
                left: 8,
                bgcolor: cameraMode === 'receipt' ? 'success.main' : 'primary.main',
                color: 'white',
                px: 1.5,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              {cameraMode === 'receipt' ? 'Receipt Mode' : 'Photo Mode'}
            </Box>

            {/* Receipt scanning guidelines */}
            {cameraMode === 'receipt' && (
              <Box
                sx={{
                  position: "absolute",
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '80%',
                  height: '60%',
                  border: '2px dashed rgba(255,255,255,0.7)',
                  borderRadius: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  pointerEvents: 'none',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: 'white',
                    bgcolor: 'rgba(0,0,0,0.6)',
                    px: 1,
                    py: 0.5,
                    borderRadius: 1,
                    textAlign: 'center',
                  }}
                >
                  Position receipt here
                </Typography>
              </Box>
            )}
          </Box>

          {/* Manual retry if video doesn't show */}
          {stream && !videoRef.current?.srcObject && (
            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                if (videoRef.current && stream) {
                  console.log('Manual retry - setting video stream');
                  videoRef.current.srcObject = stream;
                  videoRef.current.play().catch(console.error);
                }
              }}
              sx={{ mb: 2 }}
            >
              Retry Video Connection
            </Button>
          )}

          <Button
            onClick={stopCamera}
            color="error"
            size="small"
            sx={{ mt: 2, borderRadius: 20 }}
          >
            <Close fontSize="small" /> Close Camera
          </Button>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
