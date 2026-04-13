import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  ScrollView,
  Modal,
  SafeAreaView,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { getInventory, getSmartExitStrategies } from "../../src/api";

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  freshness_score: number;
  quantity: number;
  unit: string;
  purchase_date?: string;
  visual_hazard?: boolean;
  visual_verified?: boolean;
}

interface ExitStrategyScreenProps {
  navigation: any;
}

export default function ExitStrategyScreen({
  navigation,
}: ExitStrategyScreenProps) {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [strategies, setStrategies] = useState<any>(null);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [expandedActions, setExpandedActions] = useState<Set<string>>(
    new Set()
  );
  const [draftPostOpen, setDraftPostOpen] = useState(false);
  const [draftPostText, setDraftPostText] = useState("");
  const [draftCharityName, setDraftCharityName] = useState("");
  const strategiesCache = useRef<Map<string, unknown>>(new Map());

  const handleDraftPost = (charityName: string) => {
    const text = `📦 Food Donation Available\n\nHi ${charityName},\n\nI have ${selectedItem?.quantity} ${selectedItem?.unit} of ${selectedItem?.name} available for donation. It's in good condition and ready to be picked up or dropped off.\n\nPlease let me know if you can accept this donation!\n\nThank you for the great work you do! 💚`;
    setDraftPostText(text);
    setDraftCharityName(charityName);
    setDraftPostOpen(true);
  };

  const copyToClipboard = () => {
    // React Native doesn't have native clipboard by default, use Clipboard module
    Alert.alert("Draft Post", draftPostText, [
      { text: "Close", style: "cancel" },
      {
        text: "Copy Text",
        onPress: () => {
          // For native, we'd typically use react-native-clipboard or similar
          Alert.alert("Info", "Please manually copy the text from above");
        },
      },
    ]);
  };

  const loadItems = useCallback(async () => {
    try {
      const data = await getInventory();
      setItems(data);
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to load items");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  // Reload items when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      loadItems();
    }, [loadItems])
  );

  const handleSelectItem = async (item: InventoryItem) => {
    setSelectedItem(item);
    setExpandedActions(new Set());

    // Check cache
    const cachedResult = strategiesCache.current.get(item.id);
    if (cachedResult) {
      setStrategies(cachedResult);
      return;
    }

    // Fetch from API
    setStrategiesLoading(true);
    try {
      const purchaseDate = item.purchase_date
        ? new Date(item.purchase_date)
        : new Date();
      const today = new Date();
      const verified_age_days = Math.ceil(
        (today.getTime() - purchaseDate.getTime()) / (1000 * 60 * 60 * 24)
      );

      const result = await getSmartExitStrategies({
        item_name: item.name,
        category: item.category,
        freshness_score: item.freshness_score,
        quantity: item.quantity,
        unit: item.unit,
        visual_hazard: item.visual_hazard || false,
        visual_verified: item.visual_verified || false,
        verified_age_days: verified_age_days,
      });

      strategiesCache.current.set(item.id, result);
      setStrategies(result);
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to load strategies");
    } finally {
      setStrategiesLoading(false);
    }
  };

  const closeModal = () => {
    setSelectedItem(null);
    setStrategies(null);
    setExpandedActions(new Set());
  };

  const getFreshnessColor = (score: number): string => {
    if (score >= 70) return "#22c55e";
    if (score >= 50) return "#f59e0b";
    return "#ef4444";
  };

  const getSafetyColor = (level: string): string => {
    switch (level) {
      case "safe":
        return "#22c55e";
      case "warn":
        return "#f59e0b";
      case "unsafe":
        return "#ef4444";
      default:
        return "#666";
    }
  };

  const renderItemCard = ({ item }: { item: InventoryItem }) => (
    <TouchableOpacity
      style={[
        styles.itemCard,
        {
          borderColor: getFreshnessColor(item.freshness_score),
          backgroundColor:
            item.freshness_score >= 70
              ? "#f0fdf4"
              : item.freshness_score >= 50
              ? "#fffbeb"
              : "#fef2f2",
        },
      ]}
      onPress={() => handleSelectItem(item)}
    >
      <View style={styles.cardHeader}>
        <View style={styles.cardTitle}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemCategory}>{item.category}</Text>
        </View>
        <View
          style={[
            styles.scoreChip,
            { backgroundColor: getFreshnessColor(item.freshness_score) },
          ]}
        >
          <Text style={styles.scoreText}>
            {Math.round(item.freshness_score)}%
          </Text>
        </View>
      </View>
      <Text style={styles.tapText}>Tap to see options →</Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Give It a New Life</Text>
        <Text style={styles.subtitle}>
          Get recommendations for {items.length} item
          {items.length !== 1 ? "s" : ""}
        </Text>
      </View>

      {items.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>📦 Your pantry is empty</Text>
          <Text style={styles.emptySubtext}>Add items to see options</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          renderItem={renderItemCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={[styles.listContent, { paddingBottom: 80 }]}
        />
      )}

      {/* Exit Strategy Modal */}
      <Modal
        visible={!!selectedItem}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={closeModal}
      >
        <View style={styles.modal}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={closeModal}>
              <Text style={styles.closeBtn}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {selectedItem?.name} - Options
            </Text>
            <View style={{ width: 30 }} />
          </View>

          {strategiesLoading ? (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" color="#16a34a" />
            </View>
          ) : strategies?.all_options ? (
            <ScrollView style={styles.modalContent} showsVerticalScrollIndicator={false}>
              {strategies.primary_recommendation && (
                <View style={styles.recommendedBox}>
                  <Text style={styles.recommendedTitle}>
                    💡 {strategies.primary_recommendation.title}
                  </Text>
                  <View
                    style={[
                      styles.safetyChip,
                      {
                        backgroundColor: getSafetyColor(
                          strategies.primary_recommendation.safety_level
                        ),
                      },
                    ]}
                  >
                    <Text style={styles.safetyText}>
                      {strategies.primary_recommendation.safety_level.toUpperCase()}
                    </Text>
                  </View>
                </View>
              )}

              <Text style={styles.optionsTitle}>All Options:</Text>

              {strategies.all_options.map((option: any, idx: number) => (
                <View key={idx} style={styles.optionCard}>
                  <Text style={styles.optionTitle}>
                    {option.exit_path === "upcycle" && "🔄"}
                    {option.exit_path === "share" && "💝"}
                    {option.exit_path === "bin" && "🗑️"} {option.title}
                  </Text>

                  <View style={styles.chipRow}>
                    <View
                      style={[
                        styles.safetyChip,
                        {
                          backgroundColor: getSafetyColor(option.safety_level),
                        },
                      ]}
                    >
                      <Text style={styles.safetyText}>
                        {option.safety_level.toUpperCase()}
                      </Text>
                    </View>
                    {option.confidence && (
                      <Text style={styles.confidenceText}>
                        {Math.round(option.confidence)}% confidence
                      </Text>
                    )}
                  </View>

                  {option.actions && Array.isArray(option.actions) && (
                    <View style={styles.actionsList}>
                      {option.actions
                        .filter((a: any) => !a.steps || a.steps.length > 0)
                        .slice(0, 3)
                        .map((action: any, actionIdx: number) => {
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
                            <TouchableOpacity
                              key={actionIdx}
                              style={[
                                styles.actionCard,
                                isExpanded && styles.actionCardExpanded,
                              ]}
                              onPress={toggleExpand}
                            >
                              <View style={styles.actionHeader}>
                                <View style={styles.actionTitle}>
                                  <Text style={styles.actionName}>
                                    {action.title}
                                  </Text>
                                  {action.difficulty && (
                                    <Text style={styles.difficultyText}>
                                      {action.difficulty}
                                    </Text>
                                  )}
                                </View>
                                {action.steps && action.steps.length > 0 && (
                                  <Text style={styles.expandIcon}>
                                    {isExpanded ? "−" : "+"}
                                  </Text>
                                )}
                              </View>

                              {action.benefit && (
                                <Text style={styles.benefitText}>
                                  {action.benefit}
                                </Text>
                              )}

                              {option.exit_path === "share" && (
                                <TouchableOpacity
                                  style={styles.draftPostBtn}
                                  onPress={() => handleDraftPost(action.title)}
                                >
                                  <Text style={styles.draftPostBtnText}>
                                    📝 Draft Post
                                  </Text>
                                </TouchableOpacity>
                              )}

                              {isExpanded && action.steps && (
                                <View style={styles.stepsContainer}>
                                  {action.steps.map(
                                    (step: string, stepIdx: number) => (
                                      <Text key={stepIdx} style={styles.step}>
                                        {stepIdx + 1}. {step}
                                      </Text>
                                    )
                                  )}
                                </View>
                              )}
                            </TouchableOpacity>
                          );
                        })}
                    </View>
                  )}

                  {option.warnings && option.warnings.length > 0 && (
                    <View style={styles.warningsBox}>
                      {option.warnings.map((warning: string, wIdx: number) => (
                        <Text key={wIdx} style={styles.warningText}>
                          ⚠️ {warning}
                        </Text>
                      ))}
                    </View>
                  )}
                </View>
              ))}

              <View style={{ height: 40 }} />
            </ScrollView>
          ) : null}
        </View>
      </Modal>

      {/* Draft Post Modal */}
      <Modal
        visible={draftPostOpen}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setDraftPostOpen(false)}
      >
        <SafeAreaView style={styles.draftModal}>
          <View style={styles.draftModalHeader}>
            <TouchableOpacity onPress={() => setDraftPostOpen(false)}>
              <Text style={styles.closeBtn}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.draftModalTitle}>Draft for {draftCharityName}</Text>
            <View style={{ width: 30 }} />
          </View>

          <View style={styles.draftModalContent}>
            <Text style={styles.draftLabel}>Draft Post:</Text>
            <View style={styles.draftTextBox}>
              <Text style={styles.draftText}>{draftPostText}</Text>
            </View>

            <TouchableOpacity
              style={styles.copyBtn}
              onPress={copyToClipboard}
            >
              <Text style={styles.copyBtnText}>📋 Copy to Clipboard</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.closeModalBtn}
              onPress={() => setDraftPostOpen(false)}
            >
              <Text style={styles.closeModalBtnText}>Done</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: "#000",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#666",
  },
  listContent: {
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  itemCard: {
    borderWidth: 2,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  cardTitle: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
    marginBottom: 4,
  },
  itemCategory: {
    fontSize: 12,
    color: "#666",
  },
  scoreChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  scoreText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 12,
  },
  tapText: {
    fontSize: 12,
    color: "#666",
    fontStyle: "italic",
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 8,
    color: "#000",
  },
  emptySubtext: {
    fontSize: 14,
    color: "#666",
  },
  modal: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  closeBtn: {
    fontSize: 20,
    fontWeight: "600",
    color: "#666",
    width: 30,
    textAlign: "center",
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    textAlign: "center",
    flex: 1,
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  recommendedBox: {
    backgroundColor: "#f0fdf4",
    borderLeftWidth: 4,
    borderLeftColor: "#22c55e",
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  recommendedTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#065f46",
    marginBottom: 8,
  },
  optionsTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#000",
    marginBottom: 12,
  },
  optionCard: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#e2e8f0",
  },
  optionTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#000",
    marginBottom: 10,
  },
  chipRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 10,
    alignItems: "center",
  },
  safetyChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  safetyText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 11,
  },
  confidenceText: {
    fontSize: 12,
    color: "#666",
  },
  actionsList: {
    gap: 8,
  },
  actionCard: {
    backgroundColor: "#f9fafb",
    borderRadius: 8,
    padding: 10,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  actionCardExpanded: {
    backgroundColor: "#f0fdf4",
    borderColor: "#22c55e",
  },
  actionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  actionTitle: {
    flex: 1,
  },
  actionName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
    marginBottom: 4,
  },
  difficultyText: {
    fontSize: 11,
    color: "#666",
    fontWeight: "500",
  },
  expandIcon: {
    fontSize: 18,
    fontWeight: "600",
    color: "#666",
  },
  benefitText: {
    fontSize: 12,
    color: "#666",
    marginTop: 6,
  },
  stepsContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
  },
  step: {
    fontSize: 12,
    color: "#333",
    lineHeight: 18,
    marginBottom: 6,
  },
  warningsBox: {
    backgroundColor: "#fff3e0",
    padding: 10,
    borderRadius: 6,
    marginTop: 10,
  },
  warningText: {
    fontSize: 12,
    color: "#b45309",
    marginBottom: 4,
  },
  draftPostBtn: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: "#d1fae5",
    borderRadius: 6,
    borderWidth: 1,
    borderColor: "#22c55e",
    alignSelf: "flex-start",
  },
  draftPostBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#065f46",
  },
  draftModal: {
    flex: 1,
    backgroundColor: "#f8fafc",
  },
  draftModalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  draftModalTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    textAlign: "center",
    flex: 1,
  },
  draftModalContent: {
    flex: 1,
    padding: 16,
  },
  draftLabel: {
    fontSize: 14,
    fontWeight: "700",
    color: "#000",
    marginBottom: 10,
  },
  draftTextBox: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    minHeight: 200,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    marginBottom: 16,
  },
  draftText: {
    fontSize: 13,
    color: "#333",
    lineHeight: 20,
  },
  copyBtn: {
    backgroundColor: "#16a34a",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 10,
  },
  copyBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 14,
    textAlign: "center",
  },
  closeModalBtn: {
    backgroundColor: "#f1f5f9",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#cbd5e1",
  },
  closeModalBtnText: {
    color: "#333",
    fontWeight: "600",
    fontSize: 14,
    textAlign: "center",
  },
});
