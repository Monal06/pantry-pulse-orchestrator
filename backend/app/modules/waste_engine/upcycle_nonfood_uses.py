"""
Non-Food Upcycle Uses Database

Creative, sustainable ways to repurpose food items that aren't suitable for consumption.
Includes composting, gardening, crafts, and other eco-friendly uses.

Organized by food item with multiple use cases per item.
"""

NONFOOD_UPCYCLE_USES = {
    # BREAD & GRAINS
    "bread": [
        {
            "title": "Compost It",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Break into pieces and add to compost bin or garden",
            "steps": [
                "Break bread into small chunks",
                "Add to compost bin or garden compost pile",
                "Bread decomposes quickly and adds carbon",
                "Helps create nutrient-rich compost in 2-3 months"
            ]
        },
        {
            "title": "Bird Feeder",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Crumble and scatter for birds (break it up so birds don't choke)",
            "steps": [
                "Crumble bread into small pieces",
                "Scatter in garden or park for birds",
                "Best in winter when food is scarce",
                "Note: Only occasional feeding, too much bread isn't nutritious for birds"
            ]
        },
        {
            "title": "Mulch for Garden",
            "difficulty": "EASY",
            "time_mins": 15,
            "description": "Layer as mulch around plants to retain moisture",
            "steps": [
                "Break bread into chunks",
                "Layer 2-3 inches around plants (not touching stems)",
                "Add layer of wood chips on top to hide bread",
                "Bread will decompose and feed soil as it breaks down"
            ]
        },
    ],

    "rice": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Add to compost bin (brown material)",
            "steps": [
                "Cooked or uncooked rice can be composted",
                "Add to compost bin with greens (leaves, grass)",
                "Rice decomposes in 1-2 months",
                "Creates carbon-rich compost for gardens"
            ]
        },
        {
            "title": "Plant Potting Medium",
            "difficulty": "MEDIUM",
            "time_mins": 20,
            "description": "Mix with soil as drainage layer in plant pots",
            "steps": [
                "Dry out rice completely",
                "Layer at bottom of plant pots",
                "Add soil on top",
                "Rice helps with drainage, prevents root rot"
            ]
        },
        {
            "title": "Craft/Art Material",
            "difficulty": "EASY",
            "time_mins": 30,
            "description": "Use in arts and crafts projects (glue, collages, texture art)",
            "steps": [
                "Dry rice thoroughly",
                "Glue to canvas or paper for texture art",
                "Use in mosaics or craft projects",
                "Paint if desired for colored rice art"
            ]
        },
    ],

    "pasta": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Add to compost (cooked or dry)",
            "steps": [
                "Cooked pasta decomposes quickly in compost",
                "Add to bin with other browns/greens",
                "Decomposes in 1-2 months"
            ]
        },
        {
            "title": "Garden Mulch",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Layer around plants as mulch",
            "steps": [
                "Spread cooked pasta around plant base",
                "Cover with wood chips to hide",
                "Breaks down and feeds soil"
            ]
        },
        {
            "title": "Craft Art",
            "difficulty": "EASY",
            "time_mins": 45,
            "description": "Use pasta shapes for art projects, mosaics, sculptures",
            "steps": [
                "Glue pasta shapes to canvas or cardboard",
                "Create mosaics or patterns",
                "Paint if desired",
                "Great for kids' art projects"
            ]
        },
    ],

    # VEGETABLES
    "vegetable": [
        {
            "title": "Compost Pile",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Core material for compost - vegetables are 'green' materials",
            "steps": [
                "Chop vegetables into smaller pieces",
                "Layer in compost bin with browns (leaves, straw)",
                "Keep moist like wrung-out sponge",
                "Ready in 3-6 months depending on conditions"
            ]
        },
        {
            "title": "Garden Plant Food",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Bury in garden bed as fertilizer (trench composting)",
            "steps": [
                "Dig 12-inch trench in garden bed",
                "Bury vegetable scraps in trench",
                "Cover with 6 inches of soil",
                "Plant seeds/plants above in 2-4 weeks",
                "Vegetables decompose and feed growing plants"
            ]
        },
        {
            "title": "Bokashi Fermenting",
            "difficulty": "MEDIUM",
            "time_mins": 20,
            "description": "Ferment in bokashi bucket for anaerobic composting",
            "steps": [
                "Layer vegetable scraps in bokashi bucket",
                "Sprinkle bokashi bran between layers",
                "Cover and let sit 2 weeks",
                "Creates nutrient-rich 'tea' for plants",
                "Bury fermented matter in garden after"
            ]
        },
    ],

    "carrot": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Add to compost bin"
        },
        {
            "title": "Wildlife Food",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Leave scraps for rabbits, deer, or other wildlife"
        },
        {
            "title": "Dye Material",
            "difficulty": "MEDIUM",
            "time_mins": 60,
            "description": "Use carrot tops and roots for natural orange dye",
            "steps": [
                "Boil carrot scraps and tops in water",
                "Simmer 30-45 minutes",
                "Strain liquid",
                "Use dye for fabrics, paper, art projects"
            ]
        },
    ],

    "onion": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Add to compost (though can attract pests, so bury deep)"
        },
        {
            "title": "Natural Dye",
            "difficulty": "MEDIUM",
            "time_mins": 60,
            "description": "Onion skins create beautiful yellow/brown dyes",
            "steps": [
                "Collect onion skins and ends",
                "Boil in water for 30-45 minutes",
                "Strain and use for dyeing fabric or yarn",
                "Creates warm yellow to brown colors"
            ]
        },
        {
            "title": "Garden Pest Control",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Make spray to deter pests (aphids, beetles)",
            "steps": [
                "Blend onion scraps with water",
                "Let sit overnight",
                "Strain and spray on garden plants",
                "Natural pest deterrent"
            ]
        },
    ],

    "tomato": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Excellent for compost (high nitrogen)"
        },
        {
            "title": "Trench Composting",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Bury in garden to feed next season's plants"
        },
        {
            "title": "Natural Pesticide",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Tomato leaves contain alkaloids that deter pests",
            "steps": [
                "Blend diseased tomato leaves with water",
                "Let sit 24 hours",
                "Strain and spray on garden plants",
                "Helps deter aphids, spider mites, other pests"
            ]
        },
    ],

    # FRUITS
    "banana": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Excellent compost material (high potassium)"
        },
        {
            "title": "Plant Fertilizer",
            "difficulty": "EASY",
            "time_mins": 15,
            "description": "Bury banana peels around plants for potassium boost",
            "steps": [
                "Chop banana peels into pieces",
                "Bury 6 inches deep around plant base",
                "Decompose slowly, feeding plants potassium",
                "Great for tomatoes, roses, fruit trees"
            ]
        },
        {
            "title": "Banana Peel Tea",
            "difficulty": "MEDIUM",
            "time_mins": 48,
            "description": "Soak peels to make nutrient-rich plant fertilizer",
            "steps": [
                "Soak banana peels in water for 24-48 hours",
                "Strain liquid (discard peels to compost)",
                "Dilute and use as plant fertilizer",
                "High in potassium for flowering and fruiting"
            ]
        },
    ],

    "apple": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Excellent for compost, decomposes quickly"
        },
        {
            "title": "Wildlife Food",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Leave out for birds, deer, hedgehogs, etc."
        },
        {
            "title": "Apple Cider Vinegar",
            "difficulty": "HARD",
            "time_mins": 1440,
            "description": "Ferment into apple cider vinegar (30+ days process)",
            "steps": [
                "Chop apples finely",
                "Place in jar with water and sugar",
                "Cover with cloth (let air in, keep bugs out)",
                "Stir daily for 2-3 weeks",
                "Strain and let sit another 2-3 weeks",
                "Use for cleaning, pest control, cooking"
            ]
        },
    ],

    "orange": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Citrus peels decompose well in compost"
        },
        {
            "title": "All-Purpose Cleaner",
            "difficulty": "EASY",
            "time_mins": 1440,
            "description": "Soak peels in vinegar to make eco-friendly cleaner",
            "steps": [
                "Save orange/lemon peels",
                "Fill jar with peels",
                "Cover with white vinegar",
                "Let sit 2 weeks, shaking occasionally",
                "Strain and use as natural all-purpose cleaner",
                "Fresh citrus scent, degreases naturally"
            ]
        },
        {
            "title": "Citrus Oil Extraction",
            "difficulty": "EASY",
            "time_mins": 30,
            "description": "Extract oils from peels for aromatherapy or cleaning",
            "steps": [
                "Zest orange peels (collect thin colored part)",
                "Dry zest in sun or oven (low heat)",
                "Use dried zest in potpourri, tea, or infused oils",
                "Peels can be used for natural air freshener"
            ]
        },
    ],

    "strawberry": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Soft berries compost very quickly"
        },
        {
            "title": "Wildlife Snack",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Leave for birds and insects"
        },
        {
            "title": "Herbal Compost Tea",
            "difficulty": "MEDIUM",
            "time_mins": 72,
            "description": "Ferment with herbs for compost tea",
            "steps": [
                "Layer strawberries with other scraps",
                "Add herbal leaves (mint, comfrey, etc)",
                "Let ferment 2-3 days",
                "Use as plant fertilizer tea"
            ]
        },
    ],

    # DAIRY & EGGS
    "egg": [
        {
            "title": "Eggshell Compost",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Crush eggshells for garden calcium amendment",
            "steps": [
                "Rinse eggshells thoroughly",
                "Dry completely",
                "Crush into small pieces",
                "Add to compost or scatter around plants",
                "Provides calcium, deters slugs/snails"
            ]
        },
        {
            "title": "Seedling Pots",
            "difficulty": "EASY",
            "time_mins": 15,
            "description": "Use eggshell halves as biodegradable seed starters",
            "steps": [
                "Carefully crack eggs, keep half shells",
                "Rinse and dry shells",
                "Fill with potting soil",
                "Plant seeds",
                "When ready to transplant, plant whole shell directly in ground",
                "Shell decomposes and provides calcium"
            ]
        },
        {
            "title": "Craft Material",
            "difficulty": "EASY",
            "time_mins": 30,
            "description": "Use shells for mosaics, decorations, art projects"
        },
    ],

    "milk": [
        {
            "title": "Plant Fertilizer",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Dilute and use on plants for calcium and microbes",
            "steps": [
                "Dilute sour milk with water (1:1 ratio)",
                "Pour around plant base",
                "Beneficial bacteria help soil health",
                "Calcium content strengthens plants"
            ]
        },
        {
            "title": "Pest Control Spray",
            "difficulty": "EASY",
            "time_mins": 15,
            "description": "Milk spray helps prevent powdery mildew",
            "steps": [
                "Mix milk and water (1:1)",
                "Spray on plants affected by powdery mildew",
                "Repeat weekly",
                "Natural fungicide"
            ]
        },
    ],

    # PROTEINS
    "tuna": [
        {
            "title": "Compost",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Add to compost (bury deep to avoid odor and pests)",
            "steps": [
                "Chop fish into small pieces",
                "Bury 12+ inches deep in compost pile",
                "Cover well with soil/compost",
                "Becomes excellent nitrogen source (3-4 months)"
            ]
        },
        {
            "title": "Plant Fertilizer",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Make fish fertilizer tea for plants",
            "steps": [
                "Mix fish scraps with water",
                "Let sit in sealed container 1-2 weeks",
                "Strain and dilute heavily",
                "Use on plants (pungent but nutrient-rich)"
            ]
        },
    ],

    # GENERIC CATEGORIES
    "fruit": [
        {
            "title": "Compost Bin",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Excellent for compost - fruits are 'green' material",
            "steps": [
                "Add chopped fruit to compost bin",
                "Balance with brown materials (leaves, straw)",
                "Keep moist and turn occasionally",
                "Ready in 2-3 months"
            ]
        },
        {
            "title": "Wildlife Food",
            "difficulty": "EASY",
            "time_mins": 5,
            "description": "Leave out for birds, deer, hedgehogs, insects"
        },
        {
            "title": "Natural Dyes",
            "difficulty": "MEDIUM",
            "time_mins": 60,
            "description": "Different fruits create different colors for fabric dyeing",
            "steps": [
                "Boil fruit scraps in water",
                "Simmer 30-45 minutes to extract color",
                "Strain and use dye bath for fabrics",
                "Reds/purples from berries, yellows from citrus"
            ]
        },
    ],

    "vegetable": [
        {
            "title": "Compost Core",
            "difficulty": "EASY",
            "time_mins": 10,
            "description": "Vegetables are primary compost material"
        },
        {
            "title": "Garden Fertilizer",
            "difficulty": "MEDIUM",
            "time_mins": 30,
            "description": "Bury directly in garden for slow release nutrients"
        },
        {
            "title": "Bokashi Compost",
            "difficulty": "MEDIUM",
            "time_mins": 20,
            "description": "Ferment in bokashi bucket for faster composting"
        },
    ],
}


def get_nonfood_uses(item_name: str) -> list[dict]:
    """
    Get non-food upcycle uses for a specific food item.

    Args:
        item_name: e.g., "banana", "tomato", "eggshell"

    Returns:
        List of non-food use cases, or empty list if not found
    """
    return NONFOOD_UPCYCLE_USES.get(item_name.lower(), [])


def get_all_items_with_uses() -> list[str]:
    """Get list of all items with documented non-food uses"""
    return list(NONFOOD_UPCYCLE_USES.keys())


def search_uses(query: str) -> dict:
    """
    Search non-food uses by item or use type.

    Args:
        query: e.g., "compost", "banana", "dye"

    Returns:
        Dictionary mapping items to matching uses
    """
    query = query.lower()
    results = {}

    for item_name, uses in NONFOOD_UPCYCLE_USES.items():
        if query in item_name:
            results[item_name] = uses
        else:
            # Search within use titles and descriptions
            matching_uses = [
                u for u in uses
                if query in u.get("title", "").lower()
                or query in u.get("description", "").lower()
            ]
            if matching_uses:
                results[item_name] = matching_uses

    return results
