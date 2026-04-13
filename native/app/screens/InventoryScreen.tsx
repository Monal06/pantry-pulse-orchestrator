import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
  SafeAreaView,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { getInventory, deleteItem, useItem, freezeItem, cleanupInventory } from "../../src/api";

interface InventoryItem {
  id: string;
  name: string;
  category: string;
  freshness_score: number;
  freshness_status: string;
  quantity: number;
  unit: string;
  storage: string;
  is_perishable: boolean;
}

interface InventoryScreenProps {
  navigation: any;
}

export default function InventoryScreen({ navigation }: InventoryScreenProps) {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<"all" | "good" | "use_soon" | "critical">("all");

  const loadItems = useCallback(async () => {
    try {
      const data = await getInventory();
      setItems(data);
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to load inventory");
    } finally {
      setLoading(false);
      setRefreshing(false);
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

  const handleDelete = async (id: string, name: string) => {
    Alert.alert("Delete Item", `Remove ${name} from inventory?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteItem(id);
            setItems((prev) => prev.filter((i) => i.id !== id));
            Alert.alert("Success", "Item removed");
          } catch (error: any) {
            Alert.alert("Error", error.message);
          }
        },
      },
    ]);
  };

  const handleUse = async (id: string, name: string) => {
    try {
      await useItem(id, 1);
      await loadItems();
      Alert.alert("Success", `${name} marked as used`);
    } catch (error: any) {
      Alert.alert("Error", error.message);
    }
  };

  const handleFreeze = async (id: string, name: string) => {
    try {
      await freezeItem(id);
      await loadItems();
      Alert.alert("Success", `${name} moved to freezer`);
    } catch (error: any) {
      Alert.alert("Error", error.message);
    }
  };

  const getFreshnessColor = (score: number): string => {
    if (score >= 70) return "#22c55e";
    if (score >= 50) return "#f59e0b";
    return "#ef4444";
  };

  const criticalCount = items.filter((i) => i.freshness_status === "critical").length;
  const useSoonCount = items.filter((i) => i.freshness_status === "use_soon").length;
  const goodCount = items.filter((i) => i.freshness_status === "good").length;

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    return item.freshness_status === filter;
  });

  const handleCleanup = async () => {
    Alert.alert("Cleanup Inventory", "Remove noise and duplicates?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Cleanup",
        onPress: async () => {
          try {
            const result = await cleanupInventory();
            Alert.alert(
              "Success",
              `Removed ${result.removed_noise || 0} noise items, ${result.removed_duplicates || 0} duplicates`
            );
            await loadItems();
          } catch (error: any) {
            Alert.alert("Error", error.message);
          }
        },
      },
    ]);
  };

  const renderItem = ({ item }: { item: InventoryItem }) => (
    <TouchableOpacity
      style={[
        styles.itemCard,
        {
          borderLeftColor: getFreshnessColor(item.freshness_score),
          borderLeftWidth: 4,
        },
      ]}
    >
      <View style={styles.itemHeader}>
        <View style={styles.itemInfo}>
          <Text style={styles.itemName}>{item.name}</Text>
          <Text style={styles.itemCategory}>{item.category}</Text>
        </View>
        <View
          style={[
            styles.scoreChip,
            { backgroundColor: getFreshnessColor(item.freshness_score) },
          ]}
        >
          <Text style={styles.scoreText}>{Math.round(item.freshness_score)}%</Text>
        </View>
      </View>

      <View style={styles.itemMeta}>
        <Text style={styles.metaText}>
          {item.quantity} {item.unit}
        </Text>
        <Text style={styles.metaText}>📍 {item.storage}</Text>
      </View>

      <View style={styles.actionButtons}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.useBtn]}
          onPress={() => handleUse(item.id, item.name)}
        >
          <Text style={styles.actionBtnText}>✓ Use</Text>
        </TouchableOpacity>
        {item.is_perishable && item.storage !== "freezer" && (
          <TouchableOpacity
            style={[styles.actionBtn, styles.freezeBtn]}
            onPress={() => handleFreeze(item.id, item.name)}
          >
            <Text style={styles.actionBtnText}>❄️ Freeze</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.actionBtn, styles.deleteBtn]}
          onPress={() => handleDelete(item.id, item.name)}
        >
          <Text style={styles.actionBtnText}>🗑️</Text>
        </TouchableOpacity>
      </View>
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
        <View style={{ flex: 1 }}>
          <Text style={styles.title}>My Pantry</Text>
        </View>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => navigation.navigate("AddItems")}
        >
          <Text style={styles.addBtnText}>+ Add</Text>
        </TouchableOpacity>
      </View>

      {/* Filter Chips */}
      <View style={styles.filterChips}>
        {[
          { id: "all" as const, label: `All (${items.length})` },
          { id: "good" as const, label: "Fresh" },
          { id: "use_soon" as const, label: "Use Soon" },
          { id: "critical" as const, label: "Critical" },
        ].map((f) => (
          <TouchableOpacity
            key={f.id}
            style={[
              styles.filterChip,
              filter === f.id && styles.filterChipActive,
            ]}
            onPress={() => setFilter(f.id)}
          >
            <Text
              style={[
                styles.filterChipText,
                filter === f.id && styles.filterChipTextActive,
              ]}
            >
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Cleanup Button */}
      {items.length > 0 && (
        <TouchableOpacity style={styles.cleanupBtn} onPress={handleCleanup}>
          <Text style={styles.cleanupBtnText}>🧹 Clean up</Text>
        </TouchableOpacity>
      )}

      {(criticalCount > 0 || useSoonCount > 0) && (
        <View style={styles.alertBox}>
          {criticalCount > 0 && (
            <Text style={styles.alertText}>
              ⚠️ {criticalCount} item{criticalCount > 1 ? "s" : ""} need urgent
              attention
            </Text>
          )}
          {useSoonCount > 0 && (
            <Text style={styles.alertText}>
              ⏱️ {useSoonCount} item{useSoonCount > 1 ? "s" : ""} should be used
              soon
            </Text>
          )}
        </View>
      )}

      {items.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>📦 Your pantry is empty</Text>
          <Text style={styles.emptySubtext}>Add items to get started</Text>
        </View>
      ) : (
        <FlatList
          data={filtered}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={[styles.listContent, { paddingBottom: 80 }]}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => {
              setRefreshing(true);
              loadItems();
            }} />
          }
        />
      )}
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
    backgroundColor: "#f8fafc",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: "#000",
  },
  addBtn: {
    backgroundColor: "#111827",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
  },
  addBtnText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 14,
  },
  filterChips: {
    flexDirection: "row",
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: "#f1f5f9",
    borderWidth: 1,
    borderColor: "#cbd5e1",
  },
  filterChipActive: {
    backgroundColor: "#d1fae5",
    borderColor: "#22c55e",
  },
  filterChipText: {
    fontSize: 12,
    color: "#666",
    fontWeight: "600",
  },
  filterChipTextActive: {
    color: "#065f46",
  },
  cleanupBtn: {
    marginHorizontal: 12,
    marginVertical: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: "#f0fdf4",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#22c55e",
  },
  cleanupBtnText: {
    color: "#065f46",
    fontWeight: "600",
    fontSize: 12,
    textAlign: "center",
  },
  alertBox: {
    backgroundColor: "#fff8e1",
    marginHorizontal: 12,
    marginVertical: 12,
    padding: 12,
    borderRadius: 12,
  },
  alertText: {
    color: "#b45309",
    fontWeight: "600",
    fontSize: 13,
    marginVertical: 4,
  },
  listContent: {
    paddingHorizontal: 12,
    paddingBottom: 20,
  },
  itemCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  itemHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  itemInfo: {
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
  itemMeta: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 10,
  },
  metaText: {
    fontSize: 12,
    color: "#666",
  },
  actionButtons: {
    flexDirection: "row",
    gap: 8,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  useBtn: {
    backgroundColor: "#d1fae5",
  },
  freezeBtn: {
    backgroundColor: "#cffafe",
  },
  deleteBtn: {
    backgroundColor: "#fee2e2",
  },
  actionBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#000",
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
});
