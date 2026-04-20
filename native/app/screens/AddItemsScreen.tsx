import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
  SafeAreaView,
  Pressable,
} from "react-native";
import DateTimePicker from "@react-native-community/datetimepicker";
import { addManualItem, analyzeFridgePhoto, analyzeReceipt } from "../../src/api";
import * as ImagePicker from "expo-image-picker";

const CATEGORIES = [
  "vegetables",
  "fruits",
  "dairy",
  "meat",
  "bread",
  "condiments",
  "frozen",
  "other",
];

const STORAGE_OPTIONS = ["fridge", "freezer", "pantry", "counter"];

interface AddItemsScreenProps {
  navigation: any;
}

export default function AddItemsScreen({ navigation }: AddItemsScreenProps) {
  const [tab, setTab] = useState<"manual" | "camera" | "receipt">("manual");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("vegetables");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("item");
  const [storage, setStorage] = useState("fridge");
  const [isPeishable, setIsPerishable] = useState(true);
  const [purchaseDate, setPurchaseDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [purchaseDateObj, setPurchaseDateObj] = useState(new Date());

  const handleAdd = async () => {
    if (!name.trim()) {
      Alert.alert("Error", "Please enter item name");
      return;
    }

    if (!quantity || isNaN(parseFloat(quantity))) {
      Alert.alert("Error", "Please enter valid quantity");
      return;
    }

    setLoading(true);
    try {
      await addManualItem({
        name: name.trim(),
        category,
        quantity: parseFloat(quantity),
        unit,
        storage,
        is_perishable: isPeishable,
        purchase_date: purchaseDate || undefined,
      });

      Alert.alert("Success", "Item added to pantry");
      resetForm();
      navigation.goBack();
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to add item");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName("");
    setCategory("vegetables");
    setQuantity("1");
    setUnit("item");
    setStorage("fridge");
    setIsPerishable(true);
    setPurchaseDate("");
    setSelectedImage(null);
  };

  const handleDateChange = (event: any, selectedDate: any) => {
    setShowDatePicker(false);
    if (selectedDate) {
      setPurchaseDateObj(selectedDate);
      const dateStr = selectedDate.toISOString().split("T")[0];
      setPurchaseDate(dateStr);
    }
  };

  const pickImage = async (useCamera: boolean) => {
    try {
      const options: ImagePicker.ImagePickerOptions = {
        mediaTypes: ['images'] as any,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      };

      // For camera, request permission and handle simulator case
      if (useCamera) {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert(
            'Camera Permission Required',
            'Camera permission is needed to take photos. If using a simulator, please select "Choose from Library" instead.',
            [{ text: 'OK', style: 'cancel' }]
          );
          return;
        }

        try {
          const result = await ImagePicker.launchCameraAsync(options);
          if (!result.canceled) {
            await processImage(result);
          }
        } catch (cameraError: any) {
          // Simulator doesn't have camera - offer alternative
          if (cameraError.message?.includes('Camera') || cameraError.message?.includes('simulator')) {
            Alert.alert(
              'Camera Not Available',
              'Camera is not available on simulator. Would you like to choose an image from library instead?',
              [
                { text: 'Cancel', style: 'cancel' },
                { text: 'Choose from Library', onPress: () => pickImage(false) }
              ]
            );
          } else {
            throw cameraError;
          }
        }
      } else {
        // Photo library
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
          Alert.alert('Permission Denied', 'Photo library permission is required');
          return;
        }

        const result = await ImagePicker.launchImageLibraryAsync(options);
        if (!result.canceled) {
          await processImage(result);
        }
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to access media');
    }
  };

  const processImage = async (result: ImagePicker.ImagePickerResult) => {
    if (!result.assets || result.assets.length === 0) {
      Alert.alert('Error', 'No image selected');
      return;
    }

    const imageUri = result.assets[0].uri;
    setSelectedImage(imageUri);
    setLoading(true);

    try {
      const file = {
        uri: imageUri,
        type: "image/jpeg",
        name: "photo.jpg",
      } as any;

      const response =
        tab === "camera"
          ? await analyzeFridgePhoto(file)
          : await analyzeReceipt(file);

      if (response.items && response.items.length > 0) {
        setName(response.items[0].name || "");
        setCategory(response.items[0].category || "vegetables");
        setQuantity((response.items[0].quantity || 1).toString());
        setUnit(response.items[0].unit || "item");
        Alert.alert("Success", "Items extracted from photo");
      } else {
        Alert.alert("Info", "No items detected. Please add manually.");
      }
    } catch (error: any) {
      Alert.alert("Error", error.message || "Failed to analyze photo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Add Item</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {(["manual", "camera", "receipt"] as const).map((t) => (
          <Pressable
            key={t}
            style={[styles.tab, tab === t && styles.tabActive]}
            onPress={() => setTab(t)}
          >
            <Text style={[styles.tabText, tab === t && styles.tabTextActive]}>
              {t === "manual" ? "✍️ Manual" : t === "camera" ? "📷 Camera" : "📄 Receipt"}
            </Text>
          </Pressable>
        ))}
      </View>

      <ScrollView style={styles.form} showsVerticalScrollIndicator={false}>
        {/* Camera/Receipt Section */}
        {(tab === "camera" || tab === "receipt") && (
          <View style={styles.photoSection}>
            {selectedImage ? (
              <View style={styles.imagePreview}>
                <Text style={styles.imageTip}>Image selected ✓</Text>
                <TouchableOpacity
                  style={styles.changePhotoBtn}
                  onPress={() => pickImage(tab === "camera")}
                >
                  <Text style={styles.changePhotoBtnText}>
                    {tab === "camera" ? "📷 Take Another Photo" : "📄 Choose Different Receipt"}
                  </Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.photoPlaceholder}>
                <TouchableOpacity
                  style={styles.photoBtn}
                  onPress={() => pickImage(tab === "camera")}
                  disabled={loading}
                >
                  <Text style={styles.photoBtnText}>
                    {tab === "camera"
                      ? "📷 Take Fridge Photo"
                      : "📄 Choose Receipt Image"}
                  </Text>
                </TouchableOpacity>
                <Text style={styles.photoHint}>
                  {tab === "camera"
                    ? "Tap to capture fridge contents"
                    : "Tap to select receipt from library"}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Item Name */}
        <View style={styles.section}>
          <Text style={styles.label}>Item Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Apple, Milk, Bread"
            value={name}
            onChangeText={setName}
            placeholderTextColor="#999"
          />
        </View>

        {/* Category */}
        <View style={styles.section}>
          <Text style={styles.label}>Category *</Text>
          <View style={styles.categoryGrid}>
            {CATEGORIES.map((cat) => (
              <TouchableOpacity
                key={cat}
                style={[
                  styles.categoryBtn,
                  category === cat && styles.categoryBtnActive,
                ]}
                onPress={() => setCategory(cat)}
              >
                <Text
                  style={[
                    styles.categoryBtnText,
                    category === cat && styles.categoryBtnTextActive,
                  ]}
                >
                  {cat}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Quantity & Unit */}
        <View style={styles.section}>
          <View style={styles.row}>
            <View style={styles.col}>
              <Text style={styles.label}>Quantity *</Text>
              <TextInput
                style={styles.input}
                placeholder="1"
                value={quantity}
                onChangeText={setQuantity}
                keyboardType="decimal-pad"
                placeholderTextColor="#999"
              />
            </View>
            <View style={styles.col}>
              <Text style={styles.label}>Unit *</Text>
              <TextInput
                style={styles.input}
                placeholder="item"
                value={unit}
                onChangeText={setUnit}
                placeholderTextColor="#999"
              />
            </View>
          </View>
        </View>

        {/* Storage Location */}
        <View style={styles.section}>
          <Text style={styles.label}>Storage Location *</Text>
          <View style={styles.storageGrid}>
            {STORAGE_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt}
                style={[
                  styles.storageBtn,
                  storage === opt && styles.storageBtnActive,
                ]}
                onPress={() => setStorage(opt)}
              >
                <Text
                  style={[
                    styles.storageBtnText,
                    storage === opt && styles.storageBtnTextActive,
                  ]}
                >
                  {opt === "fridge"
                    ? "🧊 Fridge"
                    : opt === "freezer"
                    ? "❄️ Freezer"
                    : opt === "pantry"
                    ? "📦 Pantry"
                    : "📍 Counter"}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Perishable */}
        <View style={[styles.section, styles.switchSection]}>
          <Text style={styles.label}>Is Perishable?</Text>
          <Switch
            value={isPeishable}
            onValueChange={setIsPerishable}
            trackColor={{ false: "#ccc", true: "#81c784" }}
          />
        </View>

        {/* Purchase Date */}
        <View style={styles.section}>
          <Text style={styles.label}>Purchase Date (Optional)</Text>
          <TouchableOpacity
            style={styles.dateInput}
            onPress={() => setShowDatePicker(true)}
          >
            <Text style={styles.dateInputText}>
              📅 {purchaseDate || "Tap to select date"}
            </Text>
          </TouchableOpacity>
        </View>

        {showDatePicker && (
          <DateTimePicker
            value={purchaseDateObj}
            mode="date"
            display="spinner"
            onChange={handleDateChange}
          />
        )}

        {/* Submit Button */}
        <TouchableOpacity
          style={[styles.submitBtn, loading && styles.submitBtnDisabled]}
          onPress={handleAdd}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.submitBtnText}>✓ Add to Pantry</Text>
          )}
        </TouchableOpacity>

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
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
  },
  backBtn: {
    fontSize: 14,
    color: "#16a34a",
    fontWeight: "600",
    width: 60,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: "#000",
  },
  tabs: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: "#f1f5f9",
    borderWidth: 1,
    borderColor: "#cbd5e1",
  },
  tabActive: {
    backgroundColor: "#d1fae5",
    borderColor: "#22c55e",
  },
  tabText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#666",
    textAlign: "center",
  },
  tabTextActive: {
    color: "#065f46",
  },
  form: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  photoSection: {
    marginBottom: 24,
  },
  photoPlaceholder: {
    backgroundColor: "#f1f5f9",
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#cbd5e1",
    borderStyle: "dashed",
    padding: 24,
    alignItems: "center",
  },
  photoBtn: {
    backgroundColor: "#16a34a",
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 8,
    marginBottom: 12,
  },
  photoBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 14,
  },
  photoHint: {
    fontSize: 12,
    color: "#666",
    textAlign: "center",
  },
  imagePreview: {
    backgroundColor: "#f0fdf4",
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "#22c55e",
    padding: 16,
    alignItems: "center",
  },
  imageTip: {
    fontSize: 14,
    color: "#065f46",
    fontWeight: "600",
    marginBottom: 12,
  },
  changePhotoBtn: {
    backgroundColor: "#d1fae5",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#22c55e",
  },
  changePhotoBtnText: {
    color: "#065f46",
    fontWeight: "600",
    fontSize: 13,
  },
  dateInput: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: "#fff",
    justifyContent: "center",
  },
  dateInputText: {
    fontSize: 14,
    color: "#333",
    fontWeight: "500",
  },
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: "#000",
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: "#cbd5e1",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: "#000",
    backgroundColor: "#fff",
  },
  categoryGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  categoryBtn: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
  },
  categoryBtnActive: {
    backgroundColor: "#d1fae5",
    borderColor: "#22c55e",
  },
  categoryBtnText: {
    fontSize: 12,
    color: "#666",
    fontWeight: "500",
  },
  categoryBtnTextActive: {
    color: "#065f46",
    fontWeight: "600",
  },
  row: {
    flexDirection: "row",
    gap: 12,
  },
  col: {
    flex: 1,
  },
  storageGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  storageBtn: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#cbd5e1",
    backgroundColor: "#f1f5f9",
    flex: 1,
    minWidth: "48%",
  },
  storageBtnActive: {
    backgroundColor: "#cffafe",
    borderColor: "#0891b2",
  },
  storageBtnText: {
    fontSize: 12,
    color: "#666",
    fontWeight: "500",
    textAlign: "center",
  },
  storageBtnTextActive: {
    color: "#0c4a6e",
    fontWeight: "600",
  },
  switchSection: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderRadius: 8,
    marginBottom: 20,
  },
  submitBtn: {
    backgroundColor: "#16a34a",
    paddingVertical: 14,
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    marginTop: 12,
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
});
