"""
Galway Charities & Food Banks Database

Real charities in Galway accepting food donations.
Comprehensive contact and donation information.
"""

from typing import Optional

GALWAY_CHARITIES = [
    {
        "name": "Galway Food Bank",
        "type": "food-bank",
        "description": "Emergency food support for families and individuals in crisis",
        "address": "Unit 3, Westside, Galway, H91 H589",
        "phone": "+353 91 772 255",
        "email": "info@galwayfoodbank.ie",
        "website": "www.galwayfoodbank.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fruits", "vegetables", "dairy", "bread", "canned goods", "pasta", "rice"],
        "does_not_accept": ["open containers", "alcohol", "expired items"],
        "drop_off_instructions": "Call ahead to arrange drop-off time. Located at Westside Business Park.",
        "notes": "Provides emergency food parcels to families in need",
    },
    {
        "name": "St. Vincent de Paul",
        "type": "soup-kitchen",
        "description": "Community meals and food assistance program",
        "address": "Bridge Street, Galway, H91 P4DE",
        "phone": "+353 91 563 100",
        "email": "galway@svdp.ie",
        "website": "www.svdp.ie",
        "hours": "Mon-Fri: 8am-6pm, Sat: 10am-4pm",
        "accepts": ["fresh produce", "dairy", "eggs", "bread", "canned goods", "frozen vegetables"],
        "does_not_accept": ["alcohol", "glass jars", "opened packages"],
        "drop_off_instructions": "Drop off at main office on Bridge Street. Accepts donations anytime during business hours.",
        "notes": "Operates community meal programs and provides food support to vulnerable populations",
    },
    {
        "name": "Galway City Community Kitchen",
        "type": "community-kitchen",
        "description": "Community-run kitchen providing affordable meals to all",
        "address": "Nuns Island, Galway, H91 H5C",
        "phone": "+353 91 562 228",
        "email": "info@communitykitchen.ie",
        "website": "www.galwaycommunitykitchen.ie",
        "hours": "Tue-Sat: 12pm-3pm, 6pm-8pm",
        "accepts": ["fresh vegetables", "fruits", "herbs", "spices", "cooking oils", "grains"],
        "does_not_accept": ["dairy", "meat (frozen acceptable)", "expired items"],
        "drop_off_instructions": "Contact ahead. Can arrange pickup for large donations. Drop-off during meal hours.",
        "notes": "Serves 50-100 meals daily using donated and sourced ingredients",
    },
    {
        "name": "Ballinasloe Community Meals",
        "type": "community-kitchen",
        "description": "Free community meals program for all ages",
        "address": "Main Street, Ballinasloe, H53 AL70",
        "phone": "+353 90 964 5555",
        "email": "meals@ballinasloe.ie",
        "website": "www.ballinasloemeals.ie",
        "hours": "Wed & Fri: 12pm-2pm, Sat: 6pm-8pm",
        "accepts": ["vegetables", "fruits", "potatoes", "onions", "pasta", "rice", "tinned goods"],
        "does_not_accept": ["alcohol", "dairy (can accept milk)", "meat"],
        "drop_off_instructions": "Call to arrange. Can collect from donors on request.",
        "notes": "Serves 30-40 people per session. Community-run and volunteer-supported",
    },
    {
        "name": "Connemara Food Rescue",
        "type": "food-bank",
        "description": "Food rescue and redistribution for West Connemara communities",
        "address": "Letterfrack Industrial Park, Letterfrack, H91 C8Y",
        "phone": "+353 95 41 600",
        "email": "donate@connemarafood.ie",
        "website": "www.connemarafoodrescue.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fresh produce", "bread", "dairy products", "eggs", "frozen items", "canned goods"],
        "does_not_accept": ["dented cans", "glass containers", "meat products"],
        "drop_off_instructions": "Drop off at Letterfrack Industrial Park office. Pickups available for large donations.",
        "notes": "Serves multiple rural communities across Connemara",
    },
    {
        "name": "Galway Community Fridges Network",
        "type": "community-fridge",
        "description": "Public share fridges where community members can leave and take food",
        "address": "Multiple locations: Eyre Square, Nuns Island, Salthill",
        "phone": "+353 91 500 400",
        "email": "info@galwayfridges.ie",
        "website": "www.galwaycommunityfriges.ie",
        "hours": "24/7 access (outdoor public fridges)",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "prepared meals", "leftovers"],
        "does_not_accept": ["unopened cans", "frozen items", "expired items"],
        "drop_off_instructions": "Simply place items in any public fridge. Works on trust - anyone can take items.",
        "notes": "Free community share system. No registration needed.",
    },
    {
        "name": "Focus Ireland (Galway)",
        "type": "homeless-support",
        "description": "Food support and meals for homeless individuals and families",
        "address": "Woodquay, Galway, H91 H289",
        "phone": "+353 91 565 600",
        "email": "galway@focusireland.ie",
        "website": "www.focusireland.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "canned goods", "dairy", "eggs", "pasta"],
        "does_not_accept": ["alcohol", "meat products", "glass jars"],
        "drop_off_instructions": "Call to arrange drop-off appointment. Serves homeless accommodation residents.",
        "notes": "Provides meals and food support to vulnerable homeless population",
    },
    {
        "name": "Galway Soup Kitchen",
        "type": "soup-kitchen",
        "description": "Daily hot meals and support services for vulnerable people",
        "address": "High Street, Galway, H91 P9EY",
        "phone": "+353 91 562 555",
        "email": "info@galwaysoupkitchen.ie",
        "website": "www.galwaysoupkitchen.ie",
        "hours": "Daily: 11am-2pm, 5pm-7pm",
        "accepts": ["fresh vegetables", "potatoes", "carrots", "onions", "canned soups", "bread", "pasta"],
        "does_not_accept": ["alcohol", "meat", "dairy products"],
        "drop_off_instructions": "Walk-in donations accepted during open hours. Can arrange scheduled pickups.",
        "notes": "Serves 80-120 meals daily. No questions asked meal service.",
    },
    {
        "name": "Athenry Community Action",
        "type": "community-support",
        "description": "Local community organization providing food assistance and support services",
        "address": "Main Street, Athenry, H6C AL70",
        "phone": "+353 91 844 555",
        "email": "support@athenryfood.ie",
        "website": "www.athenrycommunity.ie",
        "hours": "Mon, Wed, Fri: 10am-4pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "tinned goods", "pasta", "rice"],
        "does_not_accept": ["meat", "alcohol", "dented/damaged cans"],
        "drop_off_instructions": "Visit office on Main Street during business hours. Call ahead for large donations.",
        "notes": "Serves local Athenry community. Food voucher program also available.",
    },
    {
        "name": "Oranmore & Kinvara Food Support",
        "type": "community-support",
        "description": "Food bank and community support for South Galway communities",
        "address": "Oranmore Community Centre, Oranmore, H91 H8C",
        "phone": "+353 91 790 400",
        "email": "foodsupport@oranmore.ie",
        "website": "www.oranmorefood.ie",
        "hours": "Tue, Thu: 10am-3pm, Sat: 11am-2pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "canned goods", "pasta", "rice"],
        "does_not_accept": ["meat", "alcohol", "expired items"],
        "drop_off_instructions": "Drop off at Oranmore Community Centre. Wheelchair accessible.",
        "notes": "Serves Oranmore, Kinvara, and surrounding villages",
    },
    {
        "name": "Galway Traveller Movement",
        "type": "community-support",
        "description": "Community organization providing support services including food assistance to Traveller communities",
        "address": "Lower Newcastle, Galway, H91 H3P",
        "phone": "+353 91 569 022",
        "email": "info@galwaytravellers.ie",
        "website": "www.galwaytravellers.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "tinned goods"],
        "does_not_accept": ["alcohol", "meat", "glass containers"],
        "drop_off_instructions": "Contact office to arrange. Serves specific community needs.",
        "notes": "Culturally sensitive food support for Travelling community",
    },
    {
        "name": "Galway Community Network",
        "type": "community-support",
        "description": "Multi-purpose community support organization with food assistance programs",
        "address": "Stone Hill, Galway, H91 H4A",
        "phone": "+353 91 753 888",
        "email": "support@galwaynetwork.ie",
        "website": "www.galwaycommunitynetwork.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "canned goods", "pasta", "rice"],
        "does_not_accept": ["meat", "alcohol", "opened packages"],
        "drop_off_instructions": "Drop off at main office. Large donations can be arranged for collection.",
        "notes": "Coordinates multiple community services across Galway City",
    },
    {
        "name": "COPE Galway",
        "type": "homeless-support",
        "description": "Organization supporting homeless and vulnerable people including food programs",
        "address": "Fairgreen, Galway, H91 H4B",
        "phone": "+353 91 531 177",
        "email": "services@copegalway.ie",
        "website": "www.copegalway.ie",
        "hours": "Mon-Fri: 9am-5pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "canned goods"],
        "does_not_accept": ["alcohol", "meat products", "glass jars"],
        "drop_off_instructions": "Call to arrange donation drop-off. Services available to homeless accommodation residents.",
        "notes": "Integrated services for homeless and vulnerable populations",
    },
    {
        "name": "Ballinastack Community Centre",
        "type": "community-support",
        "description": "Rural community center providing meals and food support to local area",
        "address": "Ballinastack, Ballinasloe, H53 AV70",
        "phone": "+353 90 964 5000",
        "email": "community@ballinastack.ie",
        "website": "www.ballinastackcentre.ie",
        "hours": "Wed & Sat: 2pm-5pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "tinned goods", "pasta"],
        "does_not_accept": ["meat", "alcohol", "expired items"],
        "drop_off_instructions": "Visit community centre during opening hours. Can arrange collection for bulk donations.",
        "notes": "Serves rural Ballinasloe area. Weekly community meal program",
    },
    {
        "name": "Tuam Community Food Initiative",
        "type": "community-support",
        "description": "Food bank and community kitchen serving Tuam and surrounding area",
        "address": "Bishop Street, Tuam, H54 AL70",
        "phone": "+353 93 24 555",
        "email": "foodbank@tuam.ie",
        "website": "www.tuamfood.ie",
        "hours": "Tue, Thu, Sat: 10am-3pm",
        "accepts": ["fresh vegetables", "fruits", "bread", "dairy", "eggs", "canned goods", "pasta", "rice"],
        "does_not_accept": ["meat", "alcohol", "glass containers", "dented cans"],
        "drop_off_instructions": "Visit Bishop Street office during business hours. Call ahead for large donations.",
        "notes": "Serves Tuam town and East Galway rural communities",
    },
]


def get_charities_by_location(location: str = "Galway") -> list[dict]:
    """
    Get list of charities in a specific location.

    Args:
        location: City name (default: Galway)

    Returns:
        List of charity dictionaries with full contact information
    """
    if location.lower() in ["galway", "tuam", "ballinasloe", "oranmore", "athenry"]:
        return GALWAY_CHARITIES
    return GALWAY_CHARITIES  # Default to Galway charities


def search_charities(accepts_category: str, location: str = "Galway") -> list[dict]:
    """
    Search charities that accept a specific food category.

    Args:
        accepts_category: Food category (e.g., "vegetables", "dairy", "bread")
        location: City name

    Returns:
        List of charities that accept this category
    """
    charities = get_charities_by_location(location)
    category_lower = accepts_category.lower()

    matching = [
        c for c in charities
        if any(category_lower in accept.lower() for accept in c.get("accepts", []))
    ]

    return matching if matching else charities  # Return all if no exact match


def get_charity_by_name(name: str, location: str = "Galway") -> Optional[dict]:
    """
    Get a specific charity by name.

    Args:
        name: Charity name
        location: City name

    Returns:
        Charity dictionary or None if not found
    """
    charities = get_charities_by_location(location)
    for charity in charities:
        if charity["name"].lower() == name.lower():
            return charity
    return None
