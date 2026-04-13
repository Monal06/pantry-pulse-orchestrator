import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  FlatList,
} from "react-native";
import { getMealSuggestions, recordCookedMeal } from "../../src/api";

interface MealsScreenProps {
  navigation: any;
}

export default function MealsScreen({ navigation }: MealsScreenProps) {
  const [meals, setMeals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMeals();
  }, []);

  const loadMeals = async () => {
    setLoading(true);
    try {
      const data = await getMealSuggestions(5);
      setMeals(data);
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to load meals");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordMeal = async (meal: any) => {
    Alert.alert(
      "Record Meal",
      `Mark "${meal.name}" as prepared?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Yes, Prepared",
          onPress: async () => {
            try {
              const ingredients = meal.ingredients || [];
              await recordCookedMeal(meal.name, ingredients);
              Alert.alert("Success", "Meal recorded!");
              loadMeals();
            } catch (error: any) {
              Alert.alert("Error", error.message);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    );
  }

  const renderMealCard = ({ item }: { item: any }) => (
    <View style={styles.mealCard}>
      <View style={styles.mealHeader}>
        <View style={styles.mealInfo}>
          <Text style={styles.mealName}>{item.name}</Text>
          {item.prep_time && (
            <Text style={styles.mealTime}>⏱️ {item.prep_time} mins</Text>
          )}
        </View>
        <View
          style={[
            styles.difficultyChip,
            {
              backgroundColor:
                item.difficulty === "easy"
                  ? "#d1fae5"
                  : item.difficulty === "medium"
                  ? "#fef3c7"
                  : "#fee2e2",
            },
          ]}
        >
          <Text style={styles.difficultyText}>
            {item.difficulty || "easy"}
          </Text>
        </View>
      </View>

      {item.description && (
        <Text style={styles.mealDescription}>{item.description}</Text>
      )}

      {item.ingredients && item.ingredients.length > 0 && (
        <View style={styles.ingredientsSection}>
          <Text style={styles.ingredientsLabel}>Ingredients:</Text>
          {item.ingredients.slice(0, 3).map((ing: string, idx: number) => (
            <Text key={idx} style={styles.ingredient}>
              • {ing}
            </Text>
          ))}
          {item.ingredients.length > 3 && (
            <Text style={styles.moreIngredients}>
              +{item.ingredients.length - 3} more
            </Text>
          )}
        </View>
      )}

      <TouchableOpacity
        style={styles.prepBtn}
        onPress={() => handleRecordMeal(item)}
      >
        <Text style={styles.prepBtnText}>✓ Mark as Prepared</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Meal Suggestions</Text>
        <Text style={styles.subtitle}>
          Based on what you have in your pantry
        </Text>
      </View>

      {meals.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>🍽️ No meal suggestions</Text>
          <Text style={styles.emptySubtext}>
            Add more items to get personalized meal ideas
          </Text>
        </View>
      ) : (
        <FlatList
          data={meals}
          renderItem={renderMealCard}
          keyExtractor={(item, idx) => idx.toString()}
          contentContainerStyle={[styles.listContent, { paddingBottom: 80 }]}
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
  mealCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  mealHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 10,
  },
  mealInfo: {
    flex: 1,
  },
  mealName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    marginBottom: 4,
  },
  mealTime: {
    fontSize: 12,
    color: "#666",
  },
  difficultyChip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
  },
  difficultyText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#000",
  },
  mealDescription: {
    fontSize: 13,
    color: "#666",
    marginBottom: 10,
    lineHeight: 18,
  },
  ingredientsSection: {
    backgroundColor: "#f9fafb",
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
  },
  ingredientsLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#000",
    marginBottom: 6,
  },
  ingredient: {
    fontSize: 12,
    color: "#666",
    lineHeight: 16,
  },
  moreIngredients: {
    fontSize: 11,
    color: "#999",
    fontStyle: "italic",
    marginTop: 4,
  },
  prepBtn: {
    backgroundColor: "#16a34a",
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  prepBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 14,
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
