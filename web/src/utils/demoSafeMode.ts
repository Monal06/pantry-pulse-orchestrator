export const DEMO_SAFE_MODE_KEY = "freshsave.demoSafeMode";
export const PRESENTATION_LOCK_KEY = "freshsave.presentationLock";

export function isDemoSafeModeEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(DEMO_SAFE_MODE_KEY) === "true";
}

export function setDemoSafeModeEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DEMO_SAFE_MODE_KEY, enabled ? "true" : "false");
}

export function isPresentationLockEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(PRESENTATION_LOCK_KEY) === "true";
}

export function setPresentationLockEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(PRESENTATION_LOCK_KEY, enabled ? "true" : "false");
  if (enabled) {
    // Presentation lock always enforces AI-free behavior.
    setDemoSafeModeEnabled(true);
  }
}

export interface PantryItemLike {
  id: string;
  name: string;
  category: string;
  quantity?: number;
  unit?: string;
  freshness_score?: number;
  freshness_status?: "good" | "use_soon" | "critical";
  visual_hazard?: boolean;
}

function scoreOf(item: PantryItemLike): number {
  return typeof item.freshness_score === "number" ? item.freshness_score : 100;
}

function statusOf(item: PantryItemLike): "good" | "use_soon" | "critical" {
  if (item.freshness_status) return item.freshness_status;
  const s = scoreOf(item);
  if (s < 50) return "critical";
  if (s < 70) return "use_soon";
  return "good";
}

function titleCase(text: string): string {
  return text
    .replace(/_/g, " ")
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function uniqueNames(items: PantryItemLike[]): string[] {
  return Array.from(new Set(items.map((i) => i.name))).slice(0, 5);
}

export function buildDemoMealSuggestions(items: PantryItemLike[]) {
  const sorted = [...items].sort((a, b) => scoreOf(a) - scoreOf(b));
  const useSoon = sorted.filter((i) => statusOf(i) === "use_soon");
  const good = sorted.filter((i) => statusOf(i) === "good");
  const eligible = sorted.filter((i) => scoreOf(i) >= 40);

  const useSoonNames = uniqueNames(useSoon);
  const allEligibleNames = uniqueNames(eligible);
  const goodNames = uniqueNames(good);

  // Never include very critical items in meal suggestions.
  const mealAIngredients = useSoonNames.length ? useSoonNames.slice(0, 4) : allEligibleNames.slice(0, 4);
  const mealBIngredients = allEligibleNames.slice(0, 4);
  const mealCIngredients = goodNames.length ? goodNames.slice(0, 4) : allEligibleNames.slice(0, 4);

  if (!allEligibleNames.length) {
    return [
      {
        name: "Fresh Starter Plate",
        description: "Current pantry items are too critical for safe meal suggestions.",
        metabolic_justification: "Defers unsafe ingredients and prioritizes safety-first cooking.",
        metabolic_score: 74,
        freshness_priority: "normal",
        prep_time_minutes: 12,
        ingredients_used: ["eggs", "rice", "beans", "frozen vegetables"],
        instructions: [
          "Set aside very critical items for disposal or non-food upcycling.",
          "Use safe staples (eggs/rice/beans/frozen veg) for a simple hot meal.",
          "Rebuild pantry with fresh produce and proteins.",
        ],
      },
    ];
  }

  return [
    {
      name: "Pantry Rescue Bowl",
      description: "Quick stir-fry bowl focused on use-soon ingredients that are still safe.",
      metabolic_justification: "Prioritizes near-expiry but safe ingredients to reduce waste without using very critical items.",
      metabolic_score: 82,
      freshness_priority: "use_soon",
      prep_time_minutes: 18,
      ingredients_used: mealAIngredients,
      instructions: [
        "Rinse and prep all use-soon ingredients into bite-size pieces.",
        "Saute harder vegetables first, then add softer items.",
        "Season with pantry staples and serve hot.",
      ],
    },
    {
      name: "Use-Soon One-Pan Meal",
      description: "A flexible one-pan meal to clear medium-priority ingredients.",
      metabolic_justification: "Converts use-soon items into a complete meal before they shift into critical risk.",
      metabolic_score: 76,
      freshness_priority: "use_soon",
      prep_time_minutes: 20,
      ingredients_used: mealBIngredients,
      instructions: [
        "Combine use-soon ingredients in a single tray or pan.",
        "Cook until proteins are done and vegetables are tender.",
        "Portion immediately and refrigerate leftovers.",
      ],
    },
    {
      name: "Balanced Fresh Mix",
      description: "A lighter plate using your freshest produce and staples.",
      metabolic_justification: "Uses fresh inventory to maintain nutrient diversity across the week.",
      metabolic_score: 88,
      freshness_priority: "normal",
      prep_time_minutes: 14,
      ingredients_used: mealCIngredients,
      instructions: [
        "Build a base with grains, bread, or legumes.",
        "Add fresh produce and one protein source.",
        "Finish with healthy fat and seasoning.",
      ],
    },
  ];
}

export function buildDemoWeeklyPlan(items: PantryItemLike[]) {
  const meals = buildDemoMealSuggestions(items);
  const criticalNames = uniqueNames(items.filter((i) => statusOf(i) === "critical"));
  const shoppingNeeded = suggestShoppingFromInventory(items);

  const days = Array.from({ length: 7 }, (_, idx) => {
    const date = new Date();
    date.setDate(date.getDate() + idx);
    const dateLabel = date.toLocaleDateString("en-US", {
      weekday: "long",
      month: "short",
      day: "numeric",
    });

    const breakfastBase = meals[idx % meals.length];
    const lunchBase = meals[(idx + 1) % meals.length];
    const dinnerBase = meals[(idx + 2) % meals.length];

    return {
      day: idx + 1,
      date_label: dateLabel,
      items_to_use_today: idx < 3 ? criticalNames.slice(0, 3) : [],
      meals: {
        breakfast: {
          name: `${breakfastBase.name} (Light)`,
          prep_time_minutes: Math.max(10, breakfastBase.prep_time_minutes - 5),
          ingredients_used: breakfastBase.ingredients_used.slice(0, 3),
        },
        lunch: {
          name: `${lunchBase.name} (Lunch)`,
          prep_time_minutes: lunchBase.prep_time_minutes,
          ingredients_used: lunchBase.ingredients_used,
        },
        dinner: {
          name: `${dinnerBase.name} (Dinner)`,
          prep_time_minutes: dinnerBase.prep_time_minutes + 5,
          ingredients_used: dinnerBase.ingredients_used,
        },
      },
    };
  });

  return {
    summary: "Demo-safe weekly plan generated from pantry inventory without external AI calls.",
    shopping_needed: shoppingNeeded,
    days,
  };
}

function suggestShoppingFromInventory(items: PantryItemLike[]): string[] {
  const categories = new Set(items.map((i) => i.category));
  const suggestions: string[] = [];
  if (!categories.has("fruit")) suggestions.push("Fresh fruit");
  if (!categories.has("vegetable")) suggestions.push("Leafy vegetables");
  if (!categories.has("meat") && !categories.has("seafood") && !categories.has("eggs")) suggestions.push("Protein option");
  if (!categories.has("dry_goods") && !categories.has("canned") && !categories.has("bread")) suggestions.push("Whole-grain staple");
  return suggestions.slice(0, 4);
}

export function buildDemoNutrition(items: PantryItemLike[]) {
  const groupMap: Record<string, string[]> = {
    protein: ["meat", "seafood", "eggs", "dairy", "canned"],
    produce: ["fruit", "vegetable"],
    fiber_carbs: ["dry_goods", "bread", "canned"],
    hydration: ["beverage"],
    healthy_fats: ["condiment", "other"],
  };

  const groupCounts: Record<string, number> = Object.fromEntries(
    Object.keys(groupMap).map((k) => [k, 0]),
  );

  for (const item of items) {
    for (const [group, categories] of Object.entries(groupMap)) {
      if (categories.includes(item.category)) {
        groupCounts[group] += 1;
      }
    }
  }

  const categories = [
    toNutritionCategory("Protein", groupCounts.protein, 2, "Add eggs, legumes, fish, or lean meat options."),
    toNutritionCategory("Produce", groupCounts.produce, 3, "Add colorful fruit and vegetables for vitamins."),
    toNutritionCategory("Fiber & Carbs", groupCounts.fiber_carbs, 2, "Add whole grains or beans for sustained energy."),
    toNutritionCategory("Hydration", groupCounts.hydration, 1, "Keep water-rich options and low-sugar drinks stocked."),
    toNutritionCategory("Healthy Fats", groupCounts.healthy_fats, 1, "Include nuts, seeds, or olive-oil based options."),
  ];

  const overallScore = Math.round(
    categories.reduce((acc, c) => acc + c.score, 0) / categories.length,
  );

  const missingFoodGroups = categories
    .filter((c) => c.status === "low")
    .map((c) => c.name);

  return {
    overall_score: overallScore,
    overall_assessment:
      overallScore >= 75
        ? "Great balance for a pantry-based week. Keep rotating perishables first."
        : overallScore >= 50
          ? "Moderate balance. Add a few missing food groups for stronger nutrition coverage."
          : "Low nutritional diversity. Add protein, produce, and whole-food staples.",
    categories,
    missing_food_groups: missingFoodGroups,
    top_recommendations: [
      "Use at-risk perishables first to preserve nutrients and reduce waste.",
      "Pair each meal with one protein + one produce source.",
      "Add one fiber-rich staple (beans, oats, whole grains) if missing.",
    ],
  };
}

function toNutritionCategory(name: string, count: number, target: number, suggestion: string) {
  const ratio = Math.min(1, count / Math.max(target, 1));
  const score = Math.round(ratio * 100);
  const status = score >= 70 ? "good" : score >= 40 ? "moderate" : "low";
  return {
    name,
    score,
    status,
    detail: `${count} pantry item${count === 1 ? "" : "s"} mapped to ${name.toLowerCase()}.`,
    suggestion,
  };
}

export function buildDemoExitStrategies(item: PantryItemLike) {
  const score = scoreOf(item);
  const visualHazard = !!item.visual_hazard;
  const highRiskCategory = item.category === "meat" || item.category === "seafood";
  const isCritical = score < 50;

  const shareSafe = !visualHazard && !isCritical && score >= (highRiskCategory ? 70 : 60);
  const upcycleSafe = !visualHazard && !isCritical && score >= (highRiskCategory ? 45 : 30);

  const shareOption = {
    exit_path: "share",
    title: "Share with Community",
    safety_level: shareSafe ? "safe" : "warn",
    confidence: shareSafe ? 85 : 60,
    actions: [
      {
        title: "Community Fridge Drop-off",
        benefit: "Helps local households while preventing waste.",
        difficulty: "easy",
        steps: [
          `Pack ${item.name} in a clean sealed container.`,
          "Add storage and best-before note.",
          "Drop at nearest community fridge during opening hours.",
        ],
      },
      {
        title: "Neighborhood Donation Post",
        benefit: "Fast peer-to-peer sharing.",
        difficulty: "easy",
        steps: [
          `Post quantity, condition, and pickup timing for ${item.name}.`,
          "Confirm recipient can collect promptly.",
        ],
      },
    ],
    warnings: shareSafe
      ? []
      : [
          "Sharing is not the top recommendation due to safety gate thresholds.",
          "Prefer immediate cooking/upcycling or safe disposal.",
        ],
  };

  const upcycleOption = {
    exit_path: "upcycle",
    title: "Upcycle at Home",
    safety_level: isCritical ? "warn" : upcycleSafe ? "safe" : "warn",
    confidence: isCritical ? 70 : upcycleSafe ? 82 : 65,
    actions: isCritical
      ? [
          {
            title: "Composting / Non-food Upcycle",
            benefit: "Safe way to return nutrients to soil without food risk.",
            difficulty: "easy",
            steps: [
              "Do not cook or consume this item—it is past safe eating stage.",
              "Compost organic material if available.",
              "Otherwise, dispose safely (see disposal option).",
            ],
          },
        ]
      : [
          {
            title: "Cook-Now Rescue Recipe",
            benefit: "Converts at-risk items into a same-day meal.",
            difficulty: "easy",
            steps: [
              `Trim and prep ${item.name} immediately.`,
              "Cook to safe internal temperature.",
              "Consume now or freeze portions right away.",
            ],
          },
          {
            title: "Freeze for Later",
            benefit: "Slows spoilage and extends usable life.",
            difficulty: "easy",
            steps: [
              `Portion ${item.name} into freezer-safe packs.`,
              "Label with date and use within 1-2 months.",
            ],
          },
          {
            title: "Non-food Upcycle",
            benefit: "Final fallback when food use is not appropriate.",
            difficulty: "easy",
            steps: [
              "For produce peels and scraps, compost where available.",
              "Use stale bread as breadcrumbs if still safe.",
            ],
          },
        ],
    warnings: isCritical
      ? [
          "⚠️ CRITICAL FRESHNESS: Do not eat or serve. Item is past safe consumption stage.",
          "Recommend composting or safe disposal only.",
        ]
      : upcycleSafe
        ? []
        : [
            "Food-use upcycling may be unsafe for this item state.",
            "Only use non-food upcycling or disposal paths.",
          ],
  };

  const binOption = {
    exit_path: "bin",
    title: "Dispose Safely",
    safety_level: "safe",
    confidence: isCritical ? 95 : 90,
    actions: [
      {
        title: isCritical ? "Safe Disposal (RECOMMENDED)" : "Safe Disposal Protocol",
        benefit: isCritical ? "Only safe option for critical-stage items." : "Prevents foodborne risk and contamination.",
        difficulty: "easy",
        steps: [
          `Seal ${item.name} securely before binning.`,
          "Separate recyclable packaging where possible.",
          "Sanitize surfaces and wash hands after handling.",
        ],
      },
    ],
    warnings: isCritical
      ? ["⚠️ Item is in CRITICAL condition—disposal is the recommended and safest choice."]
      : visualHazard
        ? ["Visual spoilage detected: disposal is strongly recommended."]
        : [],
  };

  const allOptions = isCritical ? [upcycleOption, binOption] : [upcycleOption, shareOption, binOption];

  const primaryRecommendation =
    isCritical
      ? { title: "Dispose Safely", safety_level: "safe", exit_path: "bin" }
      : shareSafe
        ? { title: "Share with Community", safety_level: "safe", exit_path: "share" }
        : upcycleSafe
          ? { title: "Upcycle at Home", safety_level: "safe", exit_path: "upcycle" }
          : { title: "Dispose Safely", safety_level: "safe", exit_path: "bin" };

  return {
    item_name: item.name,
    category: titleCase(item.category),
    freshness_status: isCritical ? "critical" : score < 70 ? "use_soon" : "good",
    primary_recommendation: primaryRecommendation,
    all_options: allOptions,
  };
}

