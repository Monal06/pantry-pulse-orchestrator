"""
Charity Finder Agent: Locate and Draft Donation Posts

When an item is in good condition but user can't consume it,
this agent:
1. Identifies local charities/food banks in Galway
2. Provides contact info and drop-off instructions
3. Suggests community sharing platforms

Uses authoritative hardcoded charities database (no Gemini).
Reliable and instant for competition demo.

Integration: Called after Exit Strategy orchestrator recommends SHARE
"""

from typing import Optional
from app.modules.waste_engine.charities_database import get_charities_by_location, search_charities


class CharityFinderAgent:
    """Find and coordinate donations for good condition items"""

    @staticmethod
    async def find_charities(
        item_name: str,
        category: str,
        quantity: float,
        unit: str,
        location: str = "Galway",
        user_address: Optional[str] = None,
    ) -> dict:
        """
        Find charities and food banks that accept donations in the area.

        Uses authoritative hardcoded charities database (no Gemini).
        Instant, reliable, and perfect for competition demo.

        Args:
            item_name: e.g., "Cheddar Cheese"
            category: e.g., "dairy"
            quantity: e.g., 500
            unit: e.g., "grams"
            location: e.g., "Galway"
            user_address: Optional address for distance calculation

        Returns:
            Dictionary with list of charities, contact info, and donation guidelines
        """
        # Get charities that accept this food category
        charities = search_charities(category, location)

        # If no exact match by category, return all charities
        if not charities:
            charities = get_charities_by_location(location)

        print(f"[CHARITY-FINDER] ✓ Found {len(charities)} charities in {location} for {category}")

        return {
            "status": "success",
            "item_name": item_name,
            "category": category,
            "charities": charities,
            "location": location,
            "message": f"Found {len(charities)} charities accepting {category} donations in {location}",
        }

    @staticmethod
    async def draft_donation_post(
        item_name: str,
        category: str,
        quantity: float,
        unit: str,
        user_name: Optional[str] = None,
        user_location: Optional[str] = None,
    ) -> dict:
        """
        Draft a donation post for community sharing platforms (e.g., community fridges, local groups).

        Args:
            item_name: e.g., "Fresh Bread"
            category: e.g., "bread"
            quantity: e.g., 2
            unit: e.g., "loaves"
            user_name: Optional name for post
            user_location: Optional specific location in city

        Returns:
            Dictionary with donation post templates for different platforms
        """
        prompt = f"""You are a community organizer helping reduce food waste.

A user wants to share/donate a food item in good condition:
- Item: {quantity} {unit} of {item_name} ({category})
- Location: {user_location or "Galway"}{f' - {user_name}' if user_name else ''}

Generate 3 donation post templates for different platforms:
1. **Community Fridge Post** (short, urgent, leave at a public fridge)
2. **Local Facebook Group Post** (friendly, community-focused)
3. **Nextdoor/Neighborhood App** (formal, with pickup details)

For each, return JSON:
{{
  "platform": "community-fridge" | "facebook" | "nextdoor",
  "title": "Catchy headline",
  "body": "Post content (2-3 sentences max)",
  "pickup_instructions": "How to claim/pick up",
  "urgency": "use-today" | "use-this-week",
  "hashtags": ["#foodwaste", "#sharing"]
}}

Make posts warm, encouraging sharing, and action-oriented.
Return JSON array with 3 posts.
"""

        try:
            response = await gemini_service._generate_with_retry(
                [types.Part.from_text(text=prompt)]
            )

            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            posts = json.loads(json_str)
            if not isinstance(posts, list):
                posts = [posts]

            return {
                "status": "success",
                "item_name": item_name,
                "posts": posts,
                "message": f"Generated donation posts for {item_name}. Ready to share!",
            }

        except Exception as e:
            return {
                "status": "error",
                "item_name": item_name,
                "error": str(e),
                "fallback_post": {
                    "platform": "community-fridge",
                    "title": f"Free: {quantity} {unit} of {item_name}",
                    "body": f"Help reduce food waste! {quantity} {unit} of fresh {item_name} available for pickup today.",
                },
            }

    @staticmethod
    async def get_donation_tips(
        item_name: str, category: str
    ) -> dict:
        """Get tips for safely donating this item"""
        prompt = f"""The user is donating {quantity} {unit} of {item_name} ({category}).

Provide 3-4 practical tips for safely packaging and donating this item:
1. How to prepare it for donation
2. Best time to drop off
3. Any temperature/storage considerations
4. Whether it needs any special packaging

Return JSON:
{{
  "preparation_tips": ["tip 1", "tip 2"],
  "packaging_suggestion": "How to package safely",
  "best_drop_off_time": "e.g., morning to ensure recipients get it while fresh",
  "special_handling": "Any special requirements"
}}
"""
        try:
            response = await gemini_service._generate_with_retry(
                [{"type": "text", "text": prompt}]
            )
            import re

            json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            return json.loads(json_str)
        except Exception as e:
            return {
                "preparation_tips": [
                    "Keep in original, sealed packaging if possible",
                    "Ensure item is cool before dropping off",
                ],
                "error": str(e),
            }


def _get_fallback_charities(location: str = "Galway") -> list[dict]:
    """Fallback list of known Galway charities when Gemini unavailable"""
    return [
        {
            "name": "Galway Food Bank",
            "type": "food-bank",
            "address": "Contact via local council",
            "notes": "Supports low-income families",
            "distance_approx_km": "varies",
        },
        {
            "name": "St. Vincent de Paul",
            "type": "soup-kitchen",
            "address": "Multiple locations in Galway",
            "notes": "Community outreach and food assistance",
            "distance_approx_km": "varies",
        },
        {
            "name": "Community Fridges Galway",
            "type": "community-fridge",
            "address": "Check Galway community groups",
            "notes": "Public fridges for food sharing",
            "distance_approx_km": "varies",
        },
    ]
