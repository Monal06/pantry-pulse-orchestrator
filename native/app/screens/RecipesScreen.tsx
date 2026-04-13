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
  Modal,
} from "react-native";
import {
  getFavoriteRecipes,
  deleteRecipe,
  toggleRecipeFavorite,
} from "../../src/api";

interface RecipesScreenProps {
  navigation: any;
}

interface Recipe {
  id: string;
  name: string;
  description: string;
  prep_time_minutes: number;
  ingredients: string[];
  instructions: string[];
  is_favorite?: boolean;
}

export default function RecipesScreen({ navigation }: RecipesScreenProps) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    setLoading(true);
    try {
      const data = await getFavoriteRecipes();
      setRecipes(data);
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to load recipes");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (id: string, name: string) => {
    Alert.alert("Delete Recipe", `Remove "${name}" from favorites?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await deleteRecipe(id);
            setRecipes((prev) => prev.filter((r) => r.id !== id));
            Alert.alert("Success", "Recipe removed");
            setSelectedRecipe(null);
          } catch (error: any) {
            Alert.alert("Error", error.message);
          }
        },
      },
    ]);
  };

  const handleToggleFavorite = async (id: string) => {
    try {
      await toggleRecipeFavorite(id);
      loadRecipes();
      setSelectedRecipe(null);
    } catch (error: any) {
      Alert.alert("Error", error.message);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#16a34a" />
      </View>
    );
  }

  const renderRecipeCard = ({ item }: { item: Recipe }) => (
    <TouchableOpacity
      style={styles.recipeCard}
      onPress={() => setSelectedRecipe(item)}
    >
      <View style={styles.recipeHeader}>
        <View style={styles.recipeInfo}>
          <Text style={styles.recipeName}>{item.name}</Text>
          {item.description && (
            <Text style={styles.recipeDescription} numberOfLines={1}>
              {item.description}
            </Text>
          )}
        </View>
        <Text style={styles.prepTime}>⏱️ {item.prep_time_minutes}m</Text>
      </View>

      {item.ingredients.length > 0 && (
        <Text style={styles.ingredientCount}>
          📦 {item.ingredients.length} ingredients
        </Text>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Saved Recipes</Text>
        <Text style={styles.subtitle}>
          {recipes.length} recipe{recipes.length !== 1 ? "s" : ""}
        </Text>
      </View>

      {recipes.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>❤️ No saved recipes</Text>
          <Text style={styles.emptySubtext}>
            Save recipes while planning meals
          </Text>
        </View>
      ) : (
        <FlatList
          data={recipes}
          renderItem={renderRecipeCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={[styles.listContent, { paddingBottom: 80 }]}
        />
      )}

      {/* Recipe Detail Modal */}
      <Modal
        visible={!!selectedRecipe}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedRecipe(null)}
      >
        {selectedRecipe && (
          <SafeAreaView style={styles.modal}>
            <View style={styles.modalHeader}>
              <TouchableOpacity onPress={() => setSelectedRecipe(null)}>
                <Text style={styles.closeBtn}>✕</Text>
              </TouchableOpacity>
              <Text style={styles.modalTitle}>{selectedRecipe.name}</Text>
              <View style={{ width: 30 }} />
            </View>

            <ScrollView
              style={styles.modalContent}
              showsVerticalScrollIndicator={false}
            >
              {selectedRecipe.description && (
                <Text style={styles.modalDescription}>
                  {selectedRecipe.description}
                </Text>
              )}

              {/* Prep Time */}
              <View style={styles.infoBox}>
                <Text style={styles.infoLabel}>⏱️ Prep Time</Text>
                <Text style={styles.infoValue}>
                  {selectedRecipe.prep_time_minutes} minutes
                </Text>
              </View>

              {/* Ingredients */}
              {selectedRecipe.ingredients.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Ingredients</Text>
                  {selectedRecipe.ingredients.map((ing, idx) => (
                    <Text key={idx} style={styles.listItem}>
                      • {ing}
                    </Text>
                  ))}
                </View>
              )}

              {/* Instructions */}
              {selectedRecipe.instructions.length > 0 && (
                <View style={styles.section}>
                  <Text style={styles.sectionTitle}>Instructions</Text>
                  {selectedRecipe.instructions.map((inst, idx) => (
                    <Text key={idx} style={styles.instruction}>
                      {idx + 1}. {inst}
                    </Text>
                  ))}
                </View>
              )}

              {/* Action Buttons */}
              <View style={styles.actionButtons}>
                <TouchableOpacity
                  style={[styles.actionBtn, styles.deleteBtn]}
                  onPress={() =>
                    handleDelete(selectedRecipe.id, selectedRecipe.name)
                  }
                >
                  <Text style={styles.deleteBtnText}>🗑️ Remove</Text>
                </TouchableOpacity>
              </View>

              <View style={{ height: 40 }} />
            </ScrollView>
          </SafeAreaView>
        )}
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
  recipeCard: {
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
  recipeHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  recipeInfo: {
    flex: 1,
  },
  recipeName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    marginBottom: 4,
  },
  recipeDescription: {
    fontSize: 12,
    color: "#666",
  },
  prepTime: {
    fontSize: 13,
    fontWeight: "600",
    color: "#666",
  },
  ingredientCount: {
    fontSize: 12,
    color: "#16a34a",
    fontWeight: "600",
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
    flex: 1,
    textAlign: "center",
  },
  modalContent: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  modalDescription: {
    fontSize: 14,
    color: "#666",
    lineHeight: 20,
    marginBottom: 16,
  },
  infoBox: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 14,
    marginBottom: 16,
  },
  infoLabel: {
    fontSize: 12,
    color: "#666",
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#000",
    marginBottom: 10,
  },
  listItem: {
    fontSize: 13,
    color: "#666",
    lineHeight: 18,
    marginBottom: 6,
  },
  instruction: {
    fontSize: 13,
    color: "#333",
    lineHeight: 20,
    marginBottom: 10,
  },
  actionButtons: {
    flexDirection: "row",
    gap: 10,
    marginTop: 20,
  },
  actionBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
  },
  deleteBtn: {
    backgroundColor: "#fee2e2",
  },
  deleteBtnText: {
    color: "#dc2626",
    fontWeight: "700",
    fontSize: 14,
  },
});
