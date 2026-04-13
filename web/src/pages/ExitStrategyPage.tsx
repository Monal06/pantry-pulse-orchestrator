import { useEffect, useState, useRef } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Chip,
  CircularProgress,
  TextField,
  Alert,
} from "@mui/material";
import { ContentCopy, Check } from "@mui/icons-material";
import {
  getInventory,
  getSmartExitStrategies,
  
} from "../api";
import { freshnessColor, freshnessLabel } from "../theme";

export default function ExitStrategyPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [exitStrategies, setExitStrategies] = useState<any>(null);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [pathResults, setPathResults] = useState<any>(null);
  const [expandedActions, setExpandedActions] = useState<Set<string>>(new Set());
  const [draftPostOpen, setDraftPostOpen] = useState(false);
  const [draftPostText, setDraftPostText] = useState("");
  const [draftCharityName, setDraftCharityName] = useState("");
  const [copySuccess, setCopySuccess] = useState(false);
  const strategiesCache = useRef<Map<string, unknown>>(new Map()); // Cache for instant loading


  // Load all items
  useEffect(() => {
    const loadItems = async () => {
      setLoading(true);
      try {
        const data = await getInventory();
        // Show ALL items - Smart Decision Engine works at ANY freshness score
        setItems(data);
      } catch (error) {
        console.error("Error loading items:", error);
      } finally {
        setLoading(false);
      }
    };
    loadItems();
  }, []);

  // Debug: Log when pathResults changes
  useEffect(() => {
    if (selectedPath === "share" && pathResults) {
      console.log("🎯 SHARE charities loaded:", pathResults);
      console.log("📍 typeof pathResults:", typeof pathResults);
      console.log("📍 Array.isArray(pathResults):", Array.isArray(pathResults));
      console.log("📍 pathResults?.charities exists:", !!pathResults?.charities);
      console.log("📍 FULL pathResults object:", JSON.stringify(pathResults, null, 2));

      if (pathResults?.charities) {
        console.log("📍 Charities array:", pathResults.charities);
        console.log("📍 Number of charities:", pathResults.charities.length);
        if (pathResults.charities[0]) {
          console.log("📍 First charity sample:", pathResults.charities[0]);
        }
      } else if (Array.isArray(pathResults)) {
        console.log("⚠️ pathResults is an ARRAY, not an object with .charities property!");
        console.log("📍 Array length:", pathResults.length);
        if (pathResults[0]) {
          console.log("📍 First item:", pathResults[0]);
        }
      }
    }
  }, [selectedPath, pathResults]);

  // Fetch exit strategies using Smart Decision Engine
  const handleSelectItem = async (item: any) => {
    setSelectedItem(item);
    setSelectedPath(null);

    // Check cache first for instant loading
    const cachedResult = strategiesCache.current.get(item.id);
    if (cachedResult) {
      console.log("[EXIT-STRATEGY] Cache hit for item:", item.id);
      setExitStrategies(cachedResult);
      return;
    }

    // Cache miss - fetch from API
    setStrategiesLoading(true);
    try {
      // Calculate verified age in days from purchase_date
      const purchaseDate = new Date(item.purchase_date);
      const today = new Date();
      const verified_age_days = Math.ceil(
        (today.getTime() - purchaseDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      // Use Smart Decision Engine - returns all options with safety gates
      const result = await getSmartExitStrategies({
        item_name: item.name,
        category: item.category,
        freshness_score: item.freshness_score,
        quantity: item.quantity,
        unit: item.unit,
        visual_hazard: item.visual_hazard || false,  // True if mold/spoilage detected
        visual_verified: item.visual_verified || false,  // True if analyzed from photo/receipt/barcode
        verified_age_days: verified_age_days,
      });
      console.log("[EXIT-STRATEGY] Smart Decision Engine result:", result);

      // Store in cache for instant future loads
      strategiesCache.current.set(item.id, result);
      setExitStrategies(result);
    } catch (error) {
      console.error("Error fetching strategies:", error);
    } finally {
      setStrategiesLoading(false);
    }
  };

  const closeModal = () => {
    setSelectedItem(null);
    setExitStrategies(null);
    setSelectedPath(null);
    setPathResults(null);
    setExpandedActions(new Set()); // Clear expanded state for fresh UX
  };

 

  const handleDraftPost = (charityName: string) => {
    const text = `📦 Food Donation Available\n\nHi ${charityName},\n\nI have ${selectedItem?.quantity} ${selectedItem?.unit} of ${selectedItem?.name} available for donation. It's in good condition and ready to be picked up or dropped off.\n\nPlease let me know if you can accept this donation!\n\nThank you for the great work you do! 💚`;
    setDraftPostText(text);
    setDraftCharityName(charityName);
    setDraftPostOpen(true);
    setCopySuccess(false);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(draftPostText).then(() => {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Give It a New Life
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Get personalized recommendations for {items.length} item{items.length !== 1 ? "s" : ""} - recipes for fresh items, sharing for aging items, disposal for critical items
        </Typography>
      </Box>

      {/* Empty State */}
      {items.length === 0 && (
        <Card sx={{ p: 4, textAlign: "center" }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            📦 Your pantry is empty
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Add items to see smart recommendations!
          </Typography>
        </Card>
      )}

      {/* Critical Items Grid */}
      <Stack spacing={2}>
        {items.map((item) => (
          <Card
            key={item.id}
            sx={{
              cursor: "pointer",
              transition: "all 0.2s",
              border: "2px solid",
              borderColor:
                item.freshness_score >= 70 ? "#4caf50" :
                item.freshness_score >= 50 ? "#ff9800" : "#d32f2f",
              bgcolor:
                item.freshness_score >= 70 ? "#f1f8e9" :
                item.freshness_score >= 50 ? "#fff8e1" : "#ffebee",
              "&:hover": {
                boxShadow: 4,
                transform: "translateY(-2px)",
              },
            }}
            onClick={() => handleSelectItem(item)}
          >
            <CardContent>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
              >
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {item.name}
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                    <Chip
                      label={freshnessLabel(item.freshness_score)}
                      size="small"
                      sx={{
                        bgcolor: freshnessColor(item.freshness_score),
                        color: "white",
                      }}
                    />
                    <Chip
                      label={`${Math.round(item.freshness_score)}%`}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                </Box>
                <Button
                  variant="contained"
                  size="small"
                  sx={{
                    bgcolor: item.freshness_score < 30 ? "#d32f2f" : "#ff9800",
                  }}
                >
                  View Options
                </Button>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {/* Exit Strategy Modal */}
      <Dialog
        open={!!selectedItem}
        onClose={closeModal}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 700, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          Give It a New Life: {selectedItem?.name}
          <Button onClick={closeModal} sx={{ minWidth: "auto" }}>✕</Button>
        </DialogTitle>

        <DialogContent sx={{ pt: 3, maxHeight: "70vh", overflow: "auto" }}>
          {/* Loading State */}
          {strategiesLoading && (
            <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 6 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Smart Decision Engine - Single Source of Truth */}
          {!strategiesLoading && selectedItem && exitStrategies?.all_options && (
            <Box>
              {exitStrategies.primary_recommendation && (
                <Card sx={{ mb: 3, bgcolor: "#e8f5e9", borderLeft: "4px solid #2e7d32" }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: "#1b5e20" }}>
                      💡 Recommended: {exitStrategies.primary_recommendation.title}
                    </Typography>
                    <Chip
                      label={`Safety: ${exitStrategies.primary_recommendation.safety_level.toUpperCase()}`}
                      size="small"
                      sx={{ mb: 2, bgcolor: "#2e7d32", color: "white" }}
                    />
                  </CardContent>
                </Card>
              )}

              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                All Options:
              </Typography>

              <Stack spacing={3}>
                {exitStrategies.all_options.map((option: any, idx: number) => (
                  <Card key={idx} sx={{ border: "1px solid #e0e0e0" }}>
                    <CardContent>
                      <Stack direction="row" justifyContent="space-between" alignItems="start" sx={{ mb: 2 }}>
                        <Box>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {option.exit_path === "upcycle" && "🔄"}
                            {option.exit_path === "share" && "💝"}
                            {option.exit_path === "bin" && "🗑️"} {option.title}
                          </Typography>
                          <Chip
                            label={`Safety: ${option.safety_level.toUpperCase()}`}
                            size="small"
                            sx={{
                              mt: 1,
                              bgcolor: option.safety_level === "safe" ? "#4caf50" : option.safety_level === "warn" ? "#ff9800" : "#d32f2f",
                              color: "white",
                            }}
                          />
                          {option.confidence && (
                            <Chip
                              label={`Confidence: ${Math.round(option.confidence)}%`}
                              size="small"
                              variant="outlined"
                              sx={{ ml: 1, mt: 1 }}
                            />
                          )}
                        </Box>
                      </Stack>

                      {option.actions && Array.isArray(option.actions) && option.actions.filter((a: any) => !a.steps || a.steps.length > 0).length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                            Actions:
                          </Typography>
                          <Stack spacing={2}>
                            {option.actions.filter((a: any) => !a.steps || a.steps.length > 0).slice(0, 3).map((action: any, actionIdx: number) => {
                              const actionKey = `${option.exit_path}-${actionIdx}`;
                              const isExpanded = expandedActions.has(actionKey);
                              const toggleExpand = () => {
                                const newSet = new Set(expandedActions);
                                if (newSet.has(actionKey)) {
                                  newSet.delete(actionKey);
                                } else {
                                  newSet.add(actionKey);
                                }
                                setExpandedActions(newSet);
                              };

                              return (
                                <Card
                                  key={actionIdx}
                                  sx={{
                                    p: 3,
                                    bgcolor: isExpanded ? "#e8f5e9" : "#fafafa",
                                    cursor: "pointer",
                                    border: "2px solid",
                                    borderColor: isExpanded ? "#4caf50" : "#e0e0e0",
                                    transition: "all 0.2s",
                                    "&:hover": { boxShadow: 2, borderColor: "#4caf50" }
                                  }}
                                  onClick={toggleExpand}
                                >
                                  <Stack direction="row" justifyContent="space-between" alignItems="start" sx={{ mb: 2 }}>
                                    <Box sx={{ flex: 1 }}>
                                      <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, fontSize: "1.2rem", color: "#1b5e20" }}>
                                        {action.title}
                                      </Typography>
                                      {action.benefit && (
                                        <Typography variant="body2" sx={{ color: "text.secondary", mb: 2, fontSize: "0.95rem" }}>
                                          {action.benefit}
                                        </Typography>
                                      )}
                                      {action.difficulty && (
                                        <Chip
                                          label={`Difficulty: ${action.difficulty.toUpperCase()}`}
                                          size="medium"
                                          sx={{
                                            mb: 2,
                                            bgcolor: action.difficulty === "easy" ? "#c8e6c9" : "#fff9c4",
                                            fontWeight: 600,
                                            fontSize: "0.9rem"
                                          }}
                                        />
                                      )}
                                      {option.exit_path === "share" && (
                                        <Button
                                          variant="outlined"
                                          size="small"
                                          sx={{ mt: 1, borderColor: "#2e7d32", color: "#2e7d32" }}
                                          onClick={() => handleDraftPost(action.title)}
                                        >
                                          📝 Draft Post
                                        </Button>
                                      )}
                                    </Box>
                                    {action?.steps && Array.isArray(action.steps) && action.steps.length > 0 && (
                                      <Box sx={{
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        width: 40,
                                        height: 40,
                                        bgcolor: isExpanded ? "#4caf50" : "#e0e0e0",
                                        borderRadius: "50%",
                                        color: isExpanded ? "white" : "#666",
                                        fontWeight: 700,
                                        fontSize: "1.5rem",
                                        ml: 2,
                                        flexShrink: 0
                                      }}>
                                        {isExpanded ? "−" : "+"}
                                      </Box>
                                    )}
                                  </Stack>

                                  {action?.steps && Array.isArray(action.steps) && (isExpanded || action.steps.length <= 3) && (
                                    <Box sx={{ mt: 2 }}>
                                      <Box component="ol" sx={{ pl: 3, m: 0, listStyleType: "decimal" }}>
                                        {isExpanded ? (
                                          action.steps.map((step: string, stepIdx: number) => (
                                            <li key={stepIdx} style={{ marginBottom: "12px" }}>
                                              <Typography variant="body2" sx={{ fontSize: "0.95rem", lineHeight: 1.6 }}>
                                                {step}
                                              </Typography>
                                            </li>
                                          ))
                                        ) : (
                                          action.steps.slice(0, 3).map((step: string, stepIdx: number) => (
                                            <li key={stepIdx} style={{ marginBottom: "12px" }}>
                                              <Typography variant="body2" sx={{ fontSize: "0.95rem", lineHeight: 1.6 }}>
                                                {step}
                                              </Typography>
                                            </li>
                                          ))
                                        )}
                                      </Box>
                                      {!isExpanded && action.steps.length > 3 && (
                                        <Typography variant="body2" sx={{ mt: 2, fontStyle: "italic", color: "primary.main", fontWeight: 600, fontSize: "0.9rem" }}>
                                          ↓ Click card to see {action.steps.length - 3} more steps
                                        </Typography>
                                      )}
                                    </Box>
                                  )}
                                </Card>
                              );
                            })}
                          </Stack>
                        </Box>
                      )}

                      {option.warnings && option.warnings.length > 0 && (
                        <Box sx={{ bgcolor: "#fff3e0", p: 1, borderRadius: 1, mt: 2 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, color: "warning.main", display: "block" }}>
                            ⚠️ Warnings:
                          </Typography>
                          {option.warnings.map((warning: string, wIdx: number) => (
                            <Typography key={wIdx} variant="caption" sx={{ display: "block", color: "warning.main" }}>
                              {warning}
                            </Typography>
                          ))}
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* Draft Post Modal */}
      <Dialog
        open={draftPostOpen}
        onClose={() => setDraftPostOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          Draft Post for {draftCharityName}
          <Button onClick={() => setDraftPostOpen(false)} sx={{ minWidth: "auto" }}>✕</Button>
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {copySuccess && (
            <Alert severity="success" sx={{ mb: 2 }}>
              ✓ Copied to clipboard!
            </Alert>
          )}
          <TextField
            fullWidth
            multiline
            rows={8}
            value={draftPostText}
            onChange={(e) => setDraftPostText(e.target.value)}
            variant="outlined"
            placeholder="Draft post will appear here..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDraftPostOpen(false)}>Cancel</Button>
          <Button
            onClick={copyToClipboard}
            variant="contained"
            startIcon={copySuccess ? <Check /> : <ContentCopy />}
          >
            {copySuccess ? "Copied!" : "Copy to Clipboard"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
