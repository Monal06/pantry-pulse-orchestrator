import { useEffect, useState } from "react";
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
  Divider,
} from "@mui/material";
import { ArrowBack } from "@mui/icons-material";
import {
  getInventory,
  getSmartExitStrategies,
  generateUpcycleRecipes,
  findCharitiesForDonation,
  getDisposalInstructions,
} from "../api";
import { freshnessColor, freshnessLabel } from "../theme";

interface ExitPathOption {
  path: string;
  icon: string;
  label: string;
  description: string;
  safety: string;
}

export default function ExitStrategyPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [exitStrategies, setExitStrategies] = useState<any>(null);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [pathResults, setPathResults] = useState<any>(null);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [expandedActions, setExpandedActions] = useState<Set<string>>(new Set());
  const [expandedCharity, setExpandedCharity] = useState<string | null>(null);
  const [showDraftMessage, setShowDraftMessage] = useState<string | null>(null);

  const exitPaths: Record<string, ExitPathOption> = {
    upcycle: {
      path: "upcycle",
      icon: "🔄",
      label: "UPCYCLE",
      description: "Use before it spoils",
      safety: "SAFE",
    },
    share: {
      path: "share",
      icon: "💝",
      label: "SHARE",
      description: "Donate to charity",
      safety: "CHECK FIRST",
    },
    bin: {
      path: "bin",
      icon: "🗑️",
      label: "BIN",
      description: "Dispose responsibly",
      safety: "SAFE",
    },
  };

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
        verified_age_days: verified_age_days,
      });
      console.log("[EXIT-STRATEGY] Smart Decision Engine result:", result);
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
  };

  const handlePathAction = async (path: string) => {
    if (!selectedItem) return;
    setResultsLoading(true);

    try {
      let results;
      if (path === "upcycle") {
        results = await generateUpcycleRecipes({
          item_name: selectedItem.name,
          category: selectedItem.category,
          freshness_score: selectedItem.freshness_score,
          quantity: selectedItem.quantity,
          unit: selectedItem.unit,
        });
        console.log("[UPCYCLE] Results from backend:", results);
      } else if (path === "share") {
        results = await findCharitiesForDonation({
          item_name: selectedItem.name,
          category: selectedItem.category,
          quantity: selectedItem.quantity,
          unit: selectedItem.unit,
        });
        console.log("[SHARE] Results from backend:", results);
      } else if (path === "bin") {
        results = await getDisposalInstructions({
          item_name: selectedItem.name,
          category: selectedItem.category,
          quantity: selectedItem.quantity,
          unit: selectedItem.unit,
        });
        console.log("[BIN] Results from backend:", results);
      }
      setPathResults(results);
    } catch (error) {
      console.error("Error fetching path results:", error);
      setPathResults({ error: "Failed to load details" });
    } finally {
      setResultsLoading(false);
    }
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
        <DialogTitle sx={{ fontWeight: 700 }}>
          Give It a New Life: {selectedItem?.name}
        </DialogTitle>

        <DialogContent sx={{ pt: 3, maxHeight: "70vh", overflow: "auto" }}>
          {/* Item Summary */}
          {selectedItem && !pathResults && (
            <Box sx={{ mb: 3, p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
              <Stack direction="row" spacing={3}>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    Freshness
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {Math.round(selectedItem.freshness_score)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    Days Old
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {Math.ceil(
                      (new Date().getTime() -
                        new Date(selectedItem.purchase_date).getTime()) /
                        (1000 * 60 * 60 * 24)
                    )}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                    Category
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    {selectedItem.category}
                  </Typography>
                </Box>
              </Stack>
              {selectedItem.freshness_score < 70 && (
                <Typography variant="body2" sx={{ mt: 2, color: "error.main" }}>
                  ⚠️ This item needs your attention soon
                </Typography>
              )}
            </Box>
          )}

          {!pathResults && <Divider sx={{ my: 3 }} />}

          {/* Loading State */}
          {(strategiesLoading || resultsLoading) && (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Smart Decision Engine renders all exit paths via option.actions - no separate pathResults needed */}
                  <Stack spacing={2}>
                    {typeof pathResults === "string" ? (
                      <Card>
                        <CardContent>
                          <Typography variant="body2">{pathResults}</Typography>
                        </CardContent>
                      </Card>
                    ) : Array.isArray(pathResults) ? (
                      pathResults.map((recipe: any, idx: number) => (
                        <Card key={idx}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {recipe.name || `Recipe ${idx + 1}`}
                            </Typography>
                            <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                              {recipe.description || "Creative recipe to use this item"}
                            </Typography>
                            {recipe.ingredients && Array.isArray(recipe.ingredients) && (
                              <Box sx={{ mt: 2, mb: 2 }}>
                                <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary" }}>
                                  Ingredients:
                                </Typography>
                                <Typography variant="body2">
                                  {recipe.ingredients.join(", ")}
                                </Typography>
                              </Box>
                            )}
                            {recipe.instructions && Array.isArray(recipe.instructions) && (
                              <Box sx={{ mt: 2, mb: 2 }}>
                                <Typography variant="caption" sx={{ fontWeight: 600, color: "text.secondary" }}>
                                  Instructions:
                                </Typography>
                                <Box component="ol" sx={{ pl: 2, my: 1 }}>
                                  {recipe.instructions.map((step: string, stepIdx: number) => (
                                    <li key={stepIdx}>
                                      <Typography variant="body2">{step}</Typography>
                                    </li>
                                  ))}
                                </Box>
                              </Box>
                            )}
                            <Stack direction="row" spacing={1} sx={{ mt: 2, flexWrap: "wrap" }}>
                              {recipe.prep_time_minutes && (
                                <Chip
                                  label={`${recipe.prep_time_minutes} mins`}
                                  size="small"
                                />
                              )}
                              {recipe.difficulty && (
                                <Chip
                                  label={`Difficulty: ${recipe.difficulty}`}
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                              {recipe.urgency_level && (
                                <Chip
                                  label={recipe.urgency_level.replace("-", " ").toUpperCase()}
                                  size="small"
                                  sx={{ bgcolor: "#ff9800", color: "white" }}
                                />
                              )}
                            </Stack>
                            {recipe.tip && (
                              <Typography variant="caption" sx={{ display: "block", mt: 2, fontStyle: "italic", color: "success.main" }}>
                                💡 {recipe.tip}
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                      ))
                    ) : pathResults?.recipes ? (
                      (Array.isArray(pathResults.recipes) ? pathResults.recipes : [pathResults.recipes]).map((recipe: any, idx: number) => (
                        <Card key={idx}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {recipe.name || `Recipe ${idx + 1}`}
                            </Typography>
                            <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                              {recipe.description || "Creative recipe to use this item"}
                            </Typography>
                          </CardContent>
                        </Card>
                      ))
                    ) : pathResults.fallback_suggestions && Array.isArray(pathResults.fallback_suggestions) ? (
                      <>
                        <Card sx={{ bgcolor: "#fff3e0", borderLeft: "4px solid #ff9800" }}>
                          <CardContent>
                            <Typography variant="body2" sx={{ color: "warning.main" }}>
                              📌 Using fallback suggestions (AI service temporarily unavailable)
                            </Typography>
                          </CardContent>
                        </Card>
                        {pathResults.fallback_suggestions.map((recipe: any, idx: number) => (
                          <Card key={idx}>
                            <CardContent>
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {recipe.name || `Recipe ${idx + 1}`}
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                                {recipe.description || "Quick recipe to use this item"}
                              </Typography>
                              {recipe.prep_time_minutes && (
                                <Chip
                                  label={`${recipe.prep_time_minutes} mins`}
                                  size="small"
                                  sx={{ mt: 2 }}
                                />
                              )}
                            </CardContent>
                          </Card>
                        ))}
                      </>
                    ) : (
                      <Card>
                        <CardContent>
                          <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mb: 2 }}>
                            Debug info (raw response):
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "0.8rem" }}>
                            {JSON.stringify(pathResults, null, 2).substring(0, 500)}
                          </Typography>
                        </CardContent>
                      </Card>
                    )}
                  </Stack>
                </Box>
              )}

              {selectedPath === "share" && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    💝 Donation Options
                  </Typography>
                  <Stack spacing={2}>
                    {typeof pathResults === "string" ? (
                      <Card>
                        <CardContent>
                          <Typography variant="body2">{pathResults}</Typography>
                        </CardContent>
                      </Card>
                    ) : Array.isArray(pathResults) ? (
                      pathResults.map((charity: any, idx: number) => (
                        <Card key={idx}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {charity.name || `Charity ${idx + 1}`}
                            </Typography>
                            <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                              {charity.description || charity.address || "Local charity accepting donations"}
                            </Typography>
                            <Stack spacing={0.5} sx={{ mt: 2 }}>
                              {charity.phone && (
                                <Typography variant="caption" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                  📞 <strong>{charity.phone}</strong>
                                </Typography>
                              )}
                              {charity.address && (
                                <Typography variant="caption" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                  📍 {charity.address}
                                </Typography>
                              )}
                              {charity.distance && (
                                <Typography variant="caption" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                  📏 {charity.distance}
                                </Typography>
                              )}
                              {charity.hours && (
                                <Typography variant="caption" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                  🕐 {charity.hours}
                                </Typography>
                              )}
                            </Stack>
                          </CardContent>
                        </Card>
                      ))
                    ) : pathResults?.charities ? (
                      (Array.isArray(pathResults.charities) ? pathResults.charities : [pathResults.charities]).map((charity: any, idx: number) => {
                        const charityKey = `${idx}-${charity.name}`;
                        const isExpanded = expandedCharity === charityKey;
                        const isDraftShowing = showDraftMessage === charityKey;
                        return (
                          <Card key={idx} sx={{ borderLeft: isExpanded ? "4px solid #4caf50" : "none" }}>
                            <CardContent>
                              <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                    {charity.name}
                                  </Typography>
                                  <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                                    {charity.description}
                                  </Typography>

                                  {/* Expanded Details Section */}
                                  {isExpanded && (
                                    <Stack spacing={1.5} sx={{ mt: 2.5 }}>
                                      {charity.phone && (
                                        <Stack direction="row" spacing={1} alignItems="flex-start">
                                          <Typography sx={{ fontWeight: 600, minWidth: "30px" }}>📞</Typography>
                                          <Box>
                                            <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                                              Phone
                                            </Typography>
                                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                              {charity.phone}
                                            </Typography>
                                          </Box>
                                        </Stack>
                                      )}

                                      {charity.address && (
                                        <Stack direction="row" spacing={1} alignItems="flex-start">
                                          <Typography sx={{ fontWeight: 600, minWidth: "30px" }}>📍</Typography>
                                          <Box>
                                            <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                                              Address
                                            </Typography>
                                            <Typography variant="body2">{charity.address}</Typography>
                                          </Box>
                                        </Stack>
                                      )}

                                      {charity.hours && (
                                        <Stack direction="row" spacing={1} alignItems="flex-start">
                                          <Typography sx={{ fontWeight: 600, minWidth: "30px" }}>🕐</Typography>
                                          <Box>
                                            <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                                              Hours
                                            </Typography>
                                            <Typography variant="body2">{charity.hours}</Typography>
                                          </Box>
                                        </Stack>
                                      )}

                                      {charity.email && (
                                        <Stack direction="row" spacing={1} alignItems="flex-start">
                                          <Typography sx={{ fontWeight: 600, minWidth: "30px" }}>✉️</Typography>
                                          <Box>
                                            <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                                              Email
                                            </Typography>
                                            <Typography variant="body2" sx={{ wordBreak: "break-all" }}>
                                              {charity.email}
                                            </Typography>
                                          </Box>
                                        </Stack>
                                      )}

                                      {charity.drop_off_instructions && (
                                        <Stack direction="row" spacing={1} alignItems="flex-start">
                                          <Typography sx={{ fontWeight: 600, minWidth: "30px" }}>📋</Typography>
                                          <Box>
                                            <Typography variant="caption" sx={{ display: "block", color: "text.secondary" }}>
                                              Drop-off Instructions
                                            </Typography>
                                            <Typography variant="body2">{charity.drop_off_instructions}</Typography>
                                          </Box>
                                        </Stack>
                                      )}

                                      {/* Draft Message Template */}
                                      {isDraftShowing && (
                                        <Box sx={{ mt: 2.5, pt: 2.5, borderTop: "1px solid #e0e0e0" }}>
                                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1.5 }}>
                                            ✍️ Draft Message
                                          </Typography>
                                          <Typography
                                            variant="body2"
                                            sx={{
                                              whiteSpace: "pre-wrap",
                                              fontFamily: "monospace",
                                              p: 2,
                                              bgcolor: "#f5f5f5",
                                              borderRadius: 1,
                                              fontSize: "0.85rem",
                                              lineHeight: 1.6,
                                              border: "1px solid #e0e0e0",
                                            }}
                                          >
{`Hi ${charity.name},

I have a fresh ${selectedItem?.name?.toUpperCase()} I'd like to donate:

• Freshness: ${Math.round(selectedItem?.freshness_score || 0)}%
• Age: ${Math.ceil(
                                            (new Date().getTime() -
                                              new Date(selectedItem?.purchase_date).getTime()) /
                                              (1000 * 60 * 60 * 24)
                                          )} days old
• Storage: Refrigerated
• Quantity: ${selectedItem?.quantity} ${selectedItem?.unit}

Is your organization currently accepting donations?
Please let me know if interested.

Thanks!`}
                                          </Typography>
                                          <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                                            <Button
                                              variant="contained"
                                              size="small"
                                              sx={{ bgcolor: "#4caf50" }}
                                              onClick={() => {
                                                const message = `Hi ${charity.name},\n\nI have a fresh ${selectedItem?.name?.toUpperCase()} I'd like to donate:\n\n• Freshness: ${Math.round(selectedItem?.freshness_score || 0)}%\n• Age: ${Math.ceil((new Date().getTime() - new Date(selectedItem?.purchase_date).getTime()) / (1000 * 60 * 60 * 24))} days old\n• Storage: Refrigerated\n• Quantity: ${selectedItem?.quantity} ${selectedItem?.unit}\n\nIs your organization currently accepting donations?\nPlease let me know if interested.\n\nThanks!`;
                                                navigator.clipboard.writeText(message);
                                                alert("✓ Message copied to clipboard!");
                                              }}
                                            >
                                              📋 Copy Message
                                            </Button>
                                            {charity.email && (
                                              <Button
                                                variant="outlined"
                                                size="small"
                                                onClick={() => {
                                                  const subject = encodeURIComponent(`Food Donation: Fresh ${selectedItem?.name}`);
                                                  const body = encodeURIComponent(`Hi ${charity.name},\n\nI have a fresh ${selectedItem?.name} I'd like to donate:\n\n• Freshness: ${Math.round(selectedItem?.freshness_score || 0)}%\n• Age: ${Math.ceil((new Date().getTime() - new Date(selectedItem?.purchase_date).getTime()) / (1000 * 60 * 60 * 24))} days old\n• Quantity: ${selectedItem?.quantity} ${selectedItem?.unit}\n\nIs your organization interested?\n\nThanks!`);
                                                  window.location.href = `mailto:${charity.email}?subject=${subject}&body=${body}`;
                                                }}
                                              >
                                                ✉️ Send Email
                                              </Button>
                                            )}
                                          </Stack>
                                        </Box>
                                      )}
                                    </Stack>
                                  )}
                                </Box>

                                {/* Action Buttons */}
                                <Stack spacing={1} sx={{ ml: 2 }}>
                                  <Button
                                    variant="contained"
                                    size="small"
                                    sx={{
                                      bgcolor: isExpanded ? "#4caf50" : "#2196f3",
                                      minWidth: "40px",
                                      fontWeight: 600,
                                      fontSize: "1.1rem"
                                    }}
                                    onClick={() => {
                                      console.log("🔘 Clicked charity expand button");
                                      console.log("   Charity:", charity.name);
                                      console.log("   charityKey:", charityKey);
                                      console.log("   isExpanded before:", isExpanded);
                                      setExpandedCharity(isExpanded ? null : charityKey);
                                    }}
                                  >
                                    {isExpanded ? "−" : "+"}
                                  </Button>
                                  {isExpanded && (
                                    <Button
                                      variant="contained"
                                      size="small"
                                      sx={{
                                        bgcolor: isDraftShowing ? "#ff9800" : "#9c27b0",
                                        fontSize: "0.75rem",
                                        minWidth: "fit-content",
                                        px: 1.5,
                                        fontWeight: 600
                                      }}
                                      onClick={() => setShowDraftMessage(isDraftShowing ? null : charityKey)}
                                    >
                                      {isDraftShowing ? "✕ Hide" : "✉️ Draft"}
                                    </Button>
                                  )}
                                </Stack>
                              </Stack>
                            </CardContent>
                          </Card>
                        );
                      })
                    ) : pathResults.fallback_charities && Array.isArray(pathResults.fallback_charities) ? (
                      <>
                        <Card sx={{ bgcolor: "#fff3e0", borderLeft: "4px solid #ff9800" }}>
                          <CardContent>
                            <Typography variant="body2" sx={{ color: "warning.main" }}>
                              📌 Using fallback charities (AI service temporarily unavailable)
                            </Typography>
                          </CardContent>
                        </Card>
                        {pathResults.fallback_charities.map((charity: any, idx: number) => (
                          <Card key={idx}>
                            <CardContent>
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {charity.name || `Charity ${idx + 1}`}
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary", my: 1 }}>
                                {charity.description || charity.address}
                              </Typography>
                            </CardContent>
                          </Card>
                        ))}
                      </>
                    ) : (
                      <Card>
                        <CardContent>
                          <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mb: 2 }}>
                            Debug info (raw response):
                          </Typography>
                          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: "0.8rem" }}>
                            {JSON.stringify(pathResults, null, 2).substring(0, 500)}
                          </Typography>
                        </CardContent>
                      </Card>
                    )}

                    {/* Draft Message Section */}
                    <Box sx={{ mt: 3, pt: 3, borderTop: "1px solid #e0e0e0" }}>
                      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                        ✍️ Draft Your Message
                      </Typography>
                      <Card sx={{ bgcolor: "#f5f5f5", mb: 2 }}>
                        <CardContent>
                          <Typography
                            variant="body2"
                            sx={{
                              whiteSpace: "pre-wrap",
                              fontFamily: "monospace",
                              p: 2,
                              bgcolor: "white",
                              borderRadius: 1,
                              border: "1px solid #e0e0e0",
                              fontSize: "0.9rem",
                              lineHeight: 1.6,
                            }}
                          >
{`Hi [Community Name],

I have a fresh ${selectedItem?.name?.toUpperCase()} I'd like to donate:

• Freshness: ${Math.round(selectedItem?.freshness_score || 0)}%
• Age: ${Math.ceil(
                              (new Date().getTime() -
                                new Date(selectedItem?.purchase_date).getTime()) /
                                (1000 * 60 * 60 * 24)
                            )} days
• Storage: Refrigerated
• Quantity: ${selectedItem?.quantity} ${selectedItem?.unit}

Is your organization currently accepting donations?
Please let me know if you'd like to receive this item.

Thanks!`}
                          </Typography>
                        </CardContent>
                      </Card>

                      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
                        <Button
                          variant="contained"
                          size="small"
                          sx={{ bgcolor: "#4caf50" }}
                          onClick={() => {
                            const message = `Hi [Community Name],\n\nI have a fresh ${selectedItem?.name?.toUpperCase()} I'd like to donate:\n\n• Freshness: ${Math.round(selectedItem?.freshness_score || 0)}%\n• Age: ${Math.ceil((new Date().getTime() - new Date(selectedItem?.purchase_date).getTime()) / (1000 * 60 * 60 * 24))} days\n• Storage: Refrigerated\n• Quantity: ${selectedItem?.quantity} ${selectedItem?.unit}\n\nIs your organization currently accepting donations?\nPlease let me know if you'd like to receive this item.\n\nThanks!`;
                            navigator.clipboard.writeText(message);
                            alert("Message copied to clipboard! 📋");
                          }}
                        >
                          📋 Copy Message
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            window.open("https://www.google.com/maps/search/food+banks+near+me", "_blank");
                          }}
                        >
                          🔍 Find Address
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            const subject = encodeURIComponent(`Food Donation: Fresh ${selectedItem?.name}`);
                            const body = encodeURIComponent(`Hi,\n\nI have a fresh ${selectedItem?.name} I'd like to donate. Please let me know if you're interested.\n\nThanks!`);
                            window.location.href = `mailto:?subject=${subject}&body=${body}`;
                          }}
                        >
                          ✉️ Send Email
                        </Button>
                      </Stack>
                    </Box>
                  </Stack>
                </Box>
              )}

              {selectedPath === "bin" && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                    🗑️ Disposal Guide
                  </Typography>
                  <Stack spacing={2}>
                    {typeof pathResults === "string" ? (
                      <Card>
                        <CardContent>
                          <Typography variant="body2">{pathResults}</Typography>
                        </CardContent>
                      </Card>
                    ) : pathResults.instructions && typeof pathResults.instructions === "object" ? (
                      <>
                        {(pathResults.instructions.primary_bin || pathResults.instructions.recommended_bin) && (
                          <Card sx={{ bgcolor: "#e3f2fd", borderLeft: "4px solid #2196f3" }}>
                            <CardContent>
                              <Stack direction="row" spacing={2} alignItems="center">
                                <Box>
                                  <Typography variant="caption" sx={{ color: "text.secondary" }}>
                                    RECOMMENDED BIN
                                  </Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 700, color: "primary.main" }}>
                                    {pathResults.instructions.primary_bin || pathResults.instructions.recommended_bin}
                                  </Typography>
                                </Box>
                                {(pathResults.instructions.bin_color || pathResults.instructions.color) && (
                                  <Box
                                    sx={{
                                      width: 40,
                                      height: 40,
                                      borderRadius: 1,
                                      bgcolor: pathResults.instructions.bin_color || pathResults.instructions.color,
                                    }}
                                  />
                                )}
                              </Stack>
                              {pathResults.instructions.reasoning && (
                                <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
                                  {pathResults.instructions.reasoning}
                                </Typography>
                              )}
                            </CardContent>
                          </Card>
                        )}

                        {pathResults.instructions.preparation_steps && Array.isArray(pathResults.instructions.preparation_steps) && (
                          <Card>
                            <CardContent>
                              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                                📋 Preparation Steps
                              </Typography>
                              <Box component="ol" sx={{ pl: 2 }}>
                                {pathResults.instructions.preparation_steps.map((step: string, idx: number) => (
                                  <li key={idx}>
                                    <Typography variant="body2" sx={{ mb: 1 }}>{step}</Typography>
                                  </li>
                                ))}
                              </Box>
                            </CardContent>
                          </Card>
                        )}

                        {pathResults.instructions.what_not_to_do && Array.isArray(pathResults.instructions.what_not_to_do) && (
                          <Card sx={{ bgcolor: "#fff3e0", borderLeft: "4px solid #ff9800" }}>
                            <CardContent>
                              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: "warning.main" }}>
                                ⚠️ What NOT to Do
                              </Typography>
                              <Box component="ul" sx={{ pl: 2 }}>
                                {pathResults.instructions.what_not_to_do.map((item: string, idx: number) => (
                                  <li key={idx}>
                                    <Typography variant="body2" sx={{ mb: 1 }}>{item}</Typography>
                                  </li>
                                ))}
                              </Box>
                            </CardContent>
                          </Card>
                        )}

                        {pathResults.instructions.environmental_impact && (
                          <Card sx={{ bgcolor: "#e8f5e9", borderLeft: "4px solid #4caf50" }}>
                            <CardContent>
                              <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, color: "success.main" }}>
                                ♻️ Environmental Impact
                              </Typography>
                              <Typography variant="body2">
                                {pathResults.instructions.environmental_impact}
                              </Typography>
                            </CardContent>
                          </Card>
                        )}
                      </>
                    ) : pathResults.instructions && typeof pathResults.instructions === "string" ? (
                      <Card>
                        <CardContent>
                          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                            {pathResults.instructions}
                          </Typography>
                        </CardContent>
                      </Card>
                    ) : pathResults.disposal_protocol ? (
                      <Card>
                        <CardContent>
                          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                            {pathResults.disposal_protocol}
                          </Typography>
                        </CardContent>
                      </Card>
                    ) : (
                      <Card sx={{ bgcolor: "#f5f5f5" }}>
                        <CardContent>
                          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                            ♻️ General Disposal Guide
                          </Typography>
                          <Stack spacing={2}>
                            <Box>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                🌍 For {selectedItem?.category?.charAt(0).toUpperCase() + selectedItem?.category?.slice(1) || "this item"}:
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                • Check your local waste management guidelines
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                • Compostable items: Add to green/compost bin if available
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                • Regular waste: Dispose in general household waste
                              </Typography>
                              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                • Never dispose of spoiled food in drain
                              </Typography>
                            </Box>
                            <Button
                              variant="outlined"
                              size="small"
                              onClick={() => window.open("https://www.google.com/search?q=waste+disposal+guidelines", "_blank")}
                            >
                              🔍 Search Disposal Guidelines
                            </Button>
                          </Stack>
                        </CardContent>
                      </Card>
                    )}
                  </Stack>
                </Box>
              )}
            </Box>
          )}

          {/* Exit Strategy Results from Smart Decision Engine */}
          {!strategiesLoading && exitStrategies?.all_options && (
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
                    {exitStrategies.primary_recommendation.warnings && exitStrategies.primary_recommendation.warnings.length > 0 && (
                      <Box sx={{ bgcolor: "#fff3e0", p: 1, borderRadius: 1, mb: 2 }}>
                        {exitStrategies.primary_recommendation.warnings.map((warning: string, idx: number) => (
                          <Typography key={idx} variant="caption" sx={{ display: "block", color: "warning.main" }}>
                            {warning}
                          </Typography>
                        ))}
                      </Box>
                    )}
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

                      {option.actions && Array.isArray(option.actions) && option.actions.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                            Actions:
                          </Typography>
                          <Stack spacing={2}>
                            {option.actions.slice(0, 3).map((action: any, actionIdx: number) => {
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
                                    </Box>
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
                                  </Stack>

                                  {action.steps && Array.isArray(action.steps) && (isExpanded || action.steps.length <= 3) && (
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

        <DialogActions sx={{ p: 2 }}>
          <Button onClick={closeModal}>Close</Button>
          {selectedPath && !pathResults && (
            <Button
              variant="contained"
              onClick={() => handlePathAction(selectedPath)}
              disabled={resultsLoading}
            >
              {selectedPath === "upcycle" && "View Recipes"}
              {selectedPath === "share" && "Find Charities"}
              {selectedPath === "bin" && "Get Disposal Guide"}
            </Button>
          )}
          {pathResults && (
            <Button variant="contained" color="success">
              ✓ Done
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
