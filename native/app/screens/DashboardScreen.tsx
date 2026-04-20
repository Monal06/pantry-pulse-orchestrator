import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
} from "react-native";
import { getInventory } from "../../src/api";

interface DashboardScreenProps {
  navigation: any;
}

export default function DashboardScreen({ navigation }: DashboardScreenProps) {
  const [stats, setStats] = useState<any>(null);
  const [inventory, setInventory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const inventoryData = await getInventory();
        setInventory(inventoryData);

        // Calculate stats from inventory
        const totalItems = inventoryData.length;
        const criticalItems = inventoryData.filter((i: any) => i.freshness_status === "critical").length;
        const useSoonItems = inventoryData.filter((i: any) => i.freshness_status === "use_soon").length;
        const goodItems = inventoryData.filter((i: any) => i.freshness_status === "good").length;

        // Calculate waste reduction percentage
        const wasteReductionPct =
          totalItems > 0
            ? Math.round(((totalItems - criticalItems) / totalItems) * 100)
            : 0;

        // Estimate CO2 saved from proper storage (1kg food = ~2.5kg CO2)
        const totalWeight = inventoryData.reduce(
          (sum: number, item: any) => sum + (item.quantity || 0),
          0
        );
        const co2Saved = (totalWeight * 2.5).toFixed(1);

        setStats({
          total_items_tracked: totalItems,
          items_good: goodItems,
          items_use_soon: useSoonItems,
          items_critical: criticalItems,
          waste_reduction_percentage: wasteReductionPct,
          co2_saved: parseFloat(co2Saved),
        });
      } catch (error) {
        console.error("Error loading dashboard:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 80 }}>
        <View style={styles.header}>
          <Text style={styles.title}>Impact Dashboard</Text>
          <Text style={styles.subtitle}>
            Your food waste reduction journey
          </Text>
        </View>

        {/* Stats Cards */}
        {stats && (
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {stats.total_items_tracked || 0}
              </Text>
              <Text style={styles.statLabel}>Items Tracked</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {stats.items_saved || 0}
              </Text>
              <Text style={styles.statLabel}>Items Saved 💚</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {stats.items_wasted || 0}
              </Text>
              <Text style={styles.statLabel}>Items Wasted</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {stats.waste_reduction_percentage?.toFixed(0)}%
              </Text>
              <Text style={styles.statLabel}>Waste Reduced</Text>
            </View>
          </View>
        )}

        {/* Stats Summary */}
        {stats && (
          <View style={styles.summaryBox}>
            <Text style={styles.summaryTitle}>Your Impact</Text>
            {stats.co2_saved && (
              <Text style={styles.summaryText}>
                ♻️ {stats.co2_saved?.toFixed(1)} kg CO₂ saved from composting
              </Text>
            )}
            {stats.money_saved && (
              <Text style={styles.summaryText}>
                💰 ${stats.money_saved?.toFixed(2)} saved on groceries
              </Text>
            )}
            {stats.items_donated && (
              <Text style={styles.summaryText}>
                🤝 {stats.items_donated || 0} items donated to community
              </Text>
            )}
          </View>
        )}

        {/* Items by Status */}
        {stats && inventory.length > 0 && (
          <View>
            {/* Critical Items */}
            {inventory.filter((i: any) => i.freshness_status === "critical").length > 0 && (
              <View style={styles.itemsSection}>
                <Text style={styles.itemsSectionTitle}>🚨 Critical Items</Text>
                {inventory
                  .filter((i: any) => i.freshness_status === "critical")
                  .map((item: any) => (
                    <View key={item.id} style={[styles.itemRow, { borderLeftColor: "#ef4444" }]}>
                      <View style={styles.itemDetails}>
                        <Text style={styles.itemName}>{item.name}</Text>
                        <Text style={styles.itemMeta}>
                          {item.quantity} {item.unit} • {item.category}
                        </Text>
                      </View>
                      <Text style={styles.freshScore}>{Math.round(item.freshness_score)}%</Text>
                    </View>
                  ))}
              </View>
            )}

            {/* Use Soon Items */}
            {inventory.filter((i: any) => i.freshness_status === "use_soon").length > 0 && (
              <View style={styles.itemsSection}>
                <Text style={styles.itemsSectionTitle}>⏱️ Use Soon</Text>
                {inventory
                  .filter((i: any) => i.freshness_status === "use_soon")
                  .map((item: any) => (
                    <View key={item.id} style={[styles.itemRow, { borderLeftColor: "#f59e0b" }]}>
                      <View style={styles.itemDetails}>
                        <Text style={styles.itemName}>{item.name}</Text>
                        <Text style={styles.itemMeta}>
                          {item.quantity} {item.unit} • {item.category}
                        </Text>
                      </View>
                      <Text style={styles.freshScore}>{Math.round(item.freshness_score)}%</Text>
                    </View>
                  ))}
              </View>
            )}

            {/* Good Items */}
            {inventory.filter((i: any) => i.freshness_status === "good").length > 0 && (
              <View style={styles.itemsSection}>
                <Text style={styles.itemsSectionTitle}>✓ Good Condition</Text>
                {inventory
                  .filter((i: any) => i.freshness_status === "good")
                  .map((item: any) => (
                    <View key={item.id} style={[styles.itemRow, { borderLeftColor: "#22c55e" }]}>
                      <View style={styles.itemDetails}>
                        <Text style={styles.itemName}>{item.name}</Text>
                        <Text style={styles.itemMeta}>
                          {item.quantity} {item.unit} • {item.category}
                        </Text>
                      </View>
                      <Text style={styles.freshScore}>{Math.round(item.freshness_score)}%</Text>
                    </View>
                  ))}
              </View>
            )}
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
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
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 12,
    paddingVertical: 12,
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: "47%",
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 24,
    fontWeight: "800",
    color: "#16a34a",
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 12,
    color: "#666",
    fontWeight: "600",
    textAlign: "center",
  },
  summaryBox: {
    marginHorizontal: 12,
    marginVertical: 12,
    backgroundColor: "#f0fdf4",
    borderLeftWidth: 4,
    borderLeftColor: "#22c55e",
    padding: 16,
    borderRadius: 8,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#065f46",
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 14,
    color: "#0f766e",
    marginBottom: 8,
    fontWeight: "500",
  },
  eventsSection: {
    marginHorizontal: 12,
    marginVertical: 12,
  },
  eventsTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    marginBottom: 12,
  },
  eventCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: "#22c55e",
  },
  eventEmoji: {
    fontSize: 18,
    marginRight: 12,
  },
  eventContent: {
    flex: 1,
  },
  eventItem: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
    marginBottom: 2,
  },
  eventTime: {
    fontSize: 12,
    color: "#666",
  },
  itemsSection: {
    marginHorizontal: 12,
    marginVertical: 16,
  },
  itemsSectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    marginBottom: 12,
  },
  itemRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderLeftWidth: 4,
  },
  itemDetails: {
    flex: 1,
  },
  itemName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
    marginBottom: 4,
  },
  itemMeta: {
    fontSize: 12,
    color: "#666",
  },
  freshScore: {
    fontSize: 14,
    fontWeight: "700",
    color: "#16a34a",
    marginLeft: 12,
  },
});
