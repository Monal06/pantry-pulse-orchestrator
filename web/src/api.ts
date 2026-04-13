const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";
const USER_ID = "demo-user";

async function request(path: string, options: RequestInit = {}) {
  const separator = path.includes("?") ? "&" : "?";
  const url = `${API_BASE_URL}${path}${separator}user_id=${USER_ID}`;
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function getInventory() {
  return request("/inventory");
}

export async function getFreshnessTiers() {
  return request("/inventory/tiers");
}

export async function addManualItem(item: {
  name: string;
  category: string;
  quantity: number;
  unit: string;
  storage: string;
  is_perishable: boolean;
  purchase_date?: string;
}) {
  return request("/inventory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(item),
  });
}

export async function deleteItem(itemId: string) {
  return request(`/inventory/${itemId}`, { method: "DELETE" });
}

export async function cleanupInventory(): Promise<{ removed_noise: number; removed_duplicates: number; total_cleaned: number }> {
  return request("/inventory/cleanup", { method: "POST" });
}

export async function useItem(itemId: string, quantity: number) {
  return request(`/inventory/${itemId}/use?quantity=${quantity}`, {
    method: "POST",
  });
}

export async function analyzeFridgePhoto(file: File) {
  const form = new FormData();
  form.append("photo", file);
  return request("/analyze/fridge-photo?auto_add=true", {
    method: "POST",
    body: form,
  });
}

export async function analyzeReceipt(file: File) {
  const form = new FormData();
  form.append("photo", file);
  return request("/analyze/receipt?auto_add=false", {
    method: "POST",
    body: form,
  });
}

export async function confirmReceiptItems(
  items: any[],
  purchaseDate: string,
  storage: string = "fridge",
) {
  return request("/inventory/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items, purchase_date: purchaseDate, storage }),
  });
}

export async function analyzeBarcode(barcode: string) {
  return request(`/analyze/barcode?barcode=${barcode}&auto_add=true`, {
    method: "POST",
  });
}

export async function checkSpoilage(file: File, itemName: string) {
  const form = new FormData();
  form.append("photo", file);
  return request(
    `/analyze/spoilage-check?item_name=${encodeURIComponent(itemName)}`,
    { method: "POST", body: form }
  );
}

export async function getMealSuggestions(count: number = 3) {
  return request(`/meals/suggestions?count=${count}`);
}

export async function recordCookedMeal(
  mealName: string,
  ingredients: string[]
) {
  const params = ingredients
    .map((i) => `ingredients_used=${encodeURIComponent(i)}`)
    .join("&");
  return request(
    `/meals/cooked?meal_name=${encodeURIComponent(mealName)}&${params}`,
    { method: "POST" }
  );
}

export async function getShoppingList() {
  return request("/shopping/list");
}

export async function freezeItem(itemId: string) {
  return request(`/inventory/${itemId}/freeze`, { method: "POST" });
}

export async function getFreezeSuggestions() {
  return request("/inventory/freeze-suggestions");
}

export async function getWasteStats() {
  return request("/waste/stats");
}

export async function getWasteEvents() {
  return request("/waste/events");
}

export async function logWasteEvent(
  itemName: string,
  category: string,
  eventType: "saved" | "wasted" | "frozen" | "donated",
  quantity: number = 1
) {
  return request(
    `/waste/log?item_name=${encodeURIComponent(itemName)}&category=${category}&event_type=${eventType}&quantity=${quantity}`,
    { method: "POST" }
  );
}

export interface DietaryProfile {
  vegetarian: boolean;
  vegan: boolean;
  gluten_free: boolean;
  dairy_free: boolean;
  nut_free: boolean;
  halal: boolean;
  kosher: boolean;
  low_carb: boolean;
  allergies: string[];
  dislikes: string[];
  cuisine_preferences: string[];
  household_size: number;
}

export async function getDietaryProfile(): Promise<DietaryProfile> {
  return request("/profile/dietary");
}

export async function updateDietaryProfile(profile: DietaryProfile) {
  return request("/profile/dietary", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
}

export async function getWeeklyMealPlan() {
  return request("/meals/weekly-plan");
}

export async function analyzeVoiceInput(text: string) {
  return request("/analyze/voice?auto_add=true", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function getNutritionalBalance() {
  return request("/analyze/nutritional-balance");
}

export async function checkNotifications() {
  return request("/notifications/check");
}

export async function getCommunityListings() {
  return request("/community/listings");
}

export async function getMyListings() {
  return request("/community/my-listings");
}

export async function createCommunityListing(data: {
  item_name: string;
  category: string;
  quantity: number;
  unit: string;
  description: string;
  pickup_location: string;
  hours_available: number;
}) {
  return request("/community/listings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function claimListing(listingId: string) {
  return request(`/community/listings/${listingId}/claim`, { method: "POST" });
}

export async function getHousehold() {
  return request("/household");
}

export async function createHousehold(name: string) {
  return request("/household/create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
}

export async function joinHousehold(code: string) {
  return request("/household/join", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}

export async function leaveHousehold() {
  return request("/household/leave", { method: "POST" });
}

export async function getFavoriteRecipes() {
  return request("/recipes/favorites");
}

export async function saveRecipe(meal: {
  name: string;
  description: string;
  ingredients: string[];
  instructions: string[];
  prep_time_minutes: number;
}) {
  const params = [
    `name=${encodeURIComponent(meal.name)}`,
    `description=${encodeURIComponent(meal.description)}`,
    `prep_time_minutes=${meal.prep_time_minutes}`,
    ...meal.ingredients.map((i) => `ingredients=${encodeURIComponent(i)}`),
    ...meal.instructions.map((i) => `instructions=${encodeURIComponent(i)}`),
  ].join("&");
  return request(`/recipes?${params}`, { method: "POST" });
}

export async function toggleRecipeFavorite(recipeId: string) {
  return request(`/recipes/${recipeId}/toggle-favorite`, { method: "POST" });
}

export async function deleteRecipe(recipeId: string) {
  return request(`/recipes/${recipeId}`, { method: "DELETE" });
}

export async function generateMetabolicPlan(payload: any) {
  return request("/recipes/metabolic/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getSmartExitStrategies(params: {
  item_name: string;
  category: string;
  freshness_score: number;
  quantity?: number;
  unit?: string;
  location?: string;
  has_garden?: boolean;
  in_office?: boolean;
  eco_priority?: string;
  visual_hazard?: boolean;
  visual_verified?: boolean;
  verified_age_days?: number;
}) {
  const queryParams = new URLSearchParams();
  queryParams.append("item_name", params.item_name);
  queryParams.append("category", params.category);
  queryParams.append("freshness_score", params.freshness_score.toString());
  if (params.quantity) queryParams.append("quantity", params.quantity.toString());
  if (params.unit) queryParams.append("unit", params.unit);
  if (params.location) queryParams.append("location", params.location);
  if (params.has_garden !== undefined) queryParams.append("has_garden", params.has_garden.toString());
  if (params.in_office !== undefined) queryParams.append("in_office", params.in_office.toString());
  if (params.eco_priority) queryParams.append("eco_priority", params.eco_priority);
  if (params.visual_hazard !== undefined) queryParams.append("visual_hazard", params.visual_hazard.toString());
  if (params.visual_verified !== undefined) queryParams.append("visual_verified", params.visual_verified.toString());
  if (params.verified_age_days !== undefined) queryParams.append("verified_age_days", params.verified_age_days.toString());

  return request(`/orchestrate/smart/exit-strategies?${queryParams.toString()}`, {
    method: "POST",
  });
}

export async function generateUpcycleRecipes(params: {
  item_name: string;
  category: string;
  freshness_score: number;
  quantity?: number;
  unit?: string;
}) {
  const queryParams = new URLSearchParams();
  queryParams.append("item_name", params.item_name);
  queryParams.append("category", params.category);
  queryParams.append("freshness_score", params.freshness_score.toString());
  if (params.quantity) queryParams.append("quantity", params.quantity.toString());
  if (params.unit) queryParams.append("unit", params.unit);

  return request(`/orchestrate/upcycle/recipes?${queryParams.toString()}`, {
    method: "POST",
  });
}

export async function findCharitiesForDonation(params: {
  item_name: string;
  category: string;
  quantity?: number;
  unit?: string;
  location?: string;
}) {
  const queryParams = new URLSearchParams();
  queryParams.append("item_name", params.item_name);
  queryParams.append("category", params.category);
  if (params.quantity) queryParams.append("quantity", params.quantity.toString());
  if (params.unit) queryParams.append("unit", params.unit);
  if (params.location) queryParams.append("location", params.location);

  return request(`/orchestrate/share/find-charities?${queryParams.toString()}`, {
    method: "POST",
  });
}

export async function getDisposalInstructions(params: {
  item_name: string;
  category: string;
  quantity?: number;
  unit?: string;
  spoilage_type?: string;
  location?: string;
}) {
  const queryParams = new URLSearchParams();
  queryParams.append("item_name", params.item_name);
  queryParams.append("category", params.category);
  if (params.quantity) queryParams.append("quantity", params.quantity.toString());
  if (params.unit) queryParams.append("unit", params.unit);
  if (params.spoilage_type) queryParams.append("spoilage_type", params.spoilage_type);
  if (params.location) queryParams.append("location", params.location);

  return request(`/orchestrate/bin/disposal-instructions?${queryParams.toString()}`, {
    method: "POST",
  });
}
