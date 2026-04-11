#!/bin/bash

# Updated Demo Script - Smart Decision Engine Testing
# Tests all 4 gates with proper parameters + SHARE & BIN scenarios
# Updated: April 10, 2026, 6:00 PM
# Status: Tests all 4-gate safety system + UPCYCLE steps + SHARE posts + BIN disposal

BASE_URL="http://localhost:8000/api/orchestrate"

echo "=========================================="
echo "SMART DECISION ENGINE - Comprehensive Demo"
echo "Version: 4-gate safety + UPCYCLE steps + SHARE posts + BIN disposal"
echo "=========================================="
echo ""

# ========================================
# SAFETY GATE TESTS (DEMO 1-6)
# ========================================

# DEMO 1: Fresh Food - All gates pass
echo "DEMO 1: Fresh Food (Score 95) - All Gates Pass"
echo "============================================"
echo "Scenario: Fresh Apple, no visual hazard, 1 day old"
echo "Expected: ALL options available (SHARE, UPCYCLE, BIN) - user can pick any"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Fresh%20Apple&category=fruits&freshness_score=95&visual_hazard=false&verified_age_days=1&location=Galway" \
  | jq '.all_options[] | {exit_path, title, safety_level}'

echo ""
echo ""

# DEMO 2: Moldy Food - Visual gate fails
echo "DEMO 2: Moldy Bread (Score 25) - Visual Hazard Gate Fails"
echo "=========================================="
echo "Scenario: Moldy bread, visual_hazard=TRUE detected"
echo "Expected: SHARE COMPLETELY HIDDEN, only UPCYCLE & BIN shown - user picks one"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Moldy%20Bread&category=bread&freshness_score=25&visual_hazard=true&verified_age_days=8&location=Galway" \
  | jq '.all_options[] | {exit_path, title, safety_level, warnings}'

echo ""
echo ""

# DEMO 3: Too Old - Age gate fails
echo "DEMO 3: Day 5 Beef (Score 20) - Age Gate Fails (meat 4-day limit)"
echo "=========================================="
echo "Scenario: 5-day-old meat, exceeds EFSA 4-day limit"
echo "Expected: SHARE option HIDDEN (age exceeds limit)"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Day%205%20Beef&category=meat&freshness_score=20&visual_hazard=false&verified_age_days=5&location=Galway" \
  | jq '.all_options[] | {exit_path, safety_level, confidence}'

echo ""
echo ""

# DEMO 4: Critical Score - Score gate fails
echo "DEMO 4: Rotten Grapes (Score 15) - Critical Score Gate Fails"
echo "=========================================="
echo "Scenario: Very old grapes, critical score"
echo "Expected: SHARE option HIDDEN (score < 20)"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Rotten%20Grapes&category=fruits&freshness_score=15&visual_hazard=true&verified_age_days=14&location=Galway" \
  | jq '.all_options[] | {exit_path, safety_level}'

echo ""
echo ""

# DEMO 5: Visual Hazard NOT PROVIDED - Missing parameter
echo "DEMO 5: Moldy Tomato (Score 30) - Visual Hazard Parameter MISSING"
echo "=========================================="
echo "Scenario: Item is moldy but visual_hazard parameter NOT passed"
echo "Expected: System adds warning BUT shows all safe options anyway"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Moldy%20Tomato&category=vegetables&freshness_score=30&verified_age_days=10&location=Galway" \
  | jq '.all_options[] | {exit_path, safety_level, warnings}'

echo ""
echo ""

# DEMO 6: Seafood (Strictest limit - 2 days)
echo "DEMO 6: Day 3 Fish (Score 30) - Seafood Age Gate (2-day limit)"
echo "=========================================="
echo "Scenario: 3-day-old fish, exceeds strictest EFSA limit"
echo "Expected: SHARE HIDDEN (3 > 2 day seafood limit)"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Day%203%20Fish&category=seafood&freshness_score=30&visual_hazard=false&verified_age_days=3&location=Galway" \
  | jq '.all_options | length as $count | "Total options: \($count)", .[] | {exit_path, safety_level}'

echo ""
echo ""

# ========================================
# UPCYCLE SCENARIOS (DEMO 7)
# ========================================

echo "=========================================="
echo "DEMO 7: UPCYCLE Steps Feature"
echo "=========================================="
echo "Shows actionable step-by-step instructions"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Aging%20Strawberries&category=fruits&freshness_score=45&visual_hazard=false&location=Galway" \
  | jq '.all_options[] | select(.exit_path=="upcycle") | {title: .title, actions: [.actions[] | {type, title, difficulty, steps}]}'

echo ""
echo ""

# ========================================
# SHARE SCENARIOS (DEMO 8-11)
# ========================================

# DEMO 8: Perfect for Share - High confidence
echo "=========================================="
echo "DEMO 8: Perfect Item for Sharing (Score 85)"
echo "=========================================="
echo "Scenario: Fresh vegetables, safe to donate"
echo "Expected: SHARE shown as SAFE with charities"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Fresh%20Broccoli&category=vegetables&freshness_score=85&visual_hazard=false&verified_age_days=2&location=Galway" \
  | jq '.all_options[] | select(.exit_path=="share") | {exit_path, title, safety_level, confidence}'

echo ""
echo ""

# DEMO 9: Marginal but Safe - Warning case
echo "=========================================="
echo "DEMO 9: Marginal Item (Score 55) - Share with Warning"
echo "=========================================="
echo "Scenario: Item is salvageable but needs caution"
echo "Expected: SHARE shown with WARNING"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Aging%20Yogurt&category=dairy&freshness_score=55&visual_hazard=false&verified_age_days=6&location=Galway" \
  | jq '.all_options[] | select(.exit_path=="share") | {exit_path, title, safety_level, warnings}'

echo ""
echo ""

# DEMO 10: Multiple quantity for donation
echo "=========================================="
echo "DEMO 10: Multiple Items for Community Fridge (Qty 10)"
echo "=========================================="
echo "Scenario: 10 apples safe to share"
echo "Expected: SHARE recommendations with quantity context"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Fresh%20Apples&category=fruits&freshness_score=80&visual_hazard=false&verified_age_days=1&quantity=10&unit=piece&location=Galway" \
  | jq '.all_options[] | select(.exit_path=="share") | {exit_path, actions}'

echo ""
echo ""

# DEMO 11: Draft Donation Post
echo "=========================================="
echo "DEMO 11: Draft Donation Post for Community Sharing"
echo "=========================================="
echo "Scenario: User wants to share fresh produce - auto-generate post"
echo "Expected: Ready-to-copy social media post"
echo ""

curl -X POST "$BASE_URL/share/draft-post?item_name=Fresh%20Apples&category=fruits&quantity=10&unit=piece&user_name=Monal" \
  | jq '.'

echo ""
echo ""

# ========================================
# BIN SCENARIOS (DEMO 12-14)
# ========================================

# DEMO 12: Critically spoiled - must dispose
echo "=========================================="
echo "DEMO 12: Critically Spoiled (Score 10) - Must Dispose"
echo "=========================================="
echo "Scenario: Item is unsafe for any use"
echo "Expected: BIN shown as only safe option"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Rotten%20Salmon&category=seafood&freshness_score=10&visual_hazard=true&verified_age_days=5&location=Galway" \
  | jq '.all_options[] | select(.exit_path=="bin") | {exit_path, title, safety_level, actions}'

echo ""
echo ""

# DEMO 13: Hazardous item - visual + age red flags
echo "=========================================="
echo "DEMO 13: Hazardous Item (Mold + Age) - Dispose Recommended"
echo "=========================================="
echo "Scenario: Multiple safety violations - visual mold AND too old"
echo "Expected: BIN as primary recommendation"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Moldy%20Leftover%20Soup&category=leftovers&freshness_score=18&visual_hazard=true&verified_age_days=6&location=Galway" \
  | jq '.primary_recommendation | {exit_path, title, safety_level}'

echo ""
echo ""

# DEMO 14: Sustainable disposal options
echo "=========================================="
echo "DEMO 14: Disposal with Sustainable Options"
echo "=========================================="
echo "Scenario: Show user eco-friendly disposal methods"
echo "Expected: BIN path with environmental guidance"
echo ""

curl -X POST "$BASE_URL/smart/exit-strategies?item_name=Spoiled%20Vegetables&category=vegetables&freshness_score=12&visual_hazard=true&verified_age_days=15&location=Galway&eco_priority=high&has_garden=true" \
  | jq '.all_options[] | select(.exit_path=="bin") | {exit_path, actions, description}'

echo ""
echo ""

# ========================================
# SUMMARY
# ========================================

echo "=========================================="
echo "Demo complete!"
echo "=========================================="
echo ""
echo "Summary of all demos:"
echo ""
echo "SAFETY GATES (DEMO 1-6):"
echo "  DEMO 1: ✅ Fresh food → All gates pass"
echo "  DEMO 2: ❌ Moldy food → Visual hazard gate fails"
echo "  DEMO 3: ❌ Too old → Age gate fails"
echo "  DEMO 4: ❌ Critical score → Score gate fails"
echo "  DEMO 5: ⚠️  Missing parameter → Warning added"
echo "  DEMO 6: ❌ Seafood too old → Age gate (strictest)"
echo ""
echo "UPCYCLE (DEMO 7):"
echo "  DEMO 7: ✅ Steps feature → Complete instructions"
echo ""
echo "SHARE (DEMO 8-11):"
echo "  DEMO 8: ✅ Perfect item → High confidence share"
echo "  DEMO 9: ⚠️  Marginal item → Share with warning"
echo "  DEMO 10: ✅ Multiple items → Quantity handling"
echo "  DEMO 11: 📝 Draft post → Auto-generate social media"
echo ""
echo "BIN (DEMO 12-14):"
echo "  DEMO 12: ❌ Critically spoiled → Must dispose"
echo "  DEMO 13: ❌ Hazardous item → Multiple red flags"
echo "  DEMO 14: ♻️  Sustainable disposal → Eco options"
echo ""
echo "Total: 14 comprehensive scenarios covering all paths"
echo ""
