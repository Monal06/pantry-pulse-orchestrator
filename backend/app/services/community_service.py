from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from app.models.community import CommunityListing, CommunityListingCreate, ListingStatus

_listings: list[CommunityListing] = []


async def create_listing(user_id: str, data: CommunityListingCreate) -> CommunityListing:
    now = datetime.utcnow()
    listing = CommunityListing(
        id=str(uuid4()),
        user_id=user_id,
        item_name=data.item_name,
        category=data.category,
        quantity=data.quantity,
        unit=data.unit,
        description=data.description,
        pickup_location=data.pickup_location,
        status=ListingStatus.AVAILABLE,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(hours=data.hours_available)).isoformat(),
    )
    _listings.append(listing)
    return listing


async def get_available_listings(exclude_user: str | None = None) -> list[CommunityListing]:
    now = datetime.utcnow().isoformat()
    results = []
    for listing in _listings:
        if listing.status != ListingStatus.AVAILABLE:
            continue
        if listing.expires_at < now:
            listing.status = ListingStatus.EXPIRED
            continue
        if exclude_user and listing.user_id == exclude_user:
            continue
        results.append(listing)
    return results


async def get_my_listings(user_id: str) -> list[CommunityListing]:
    return [l for l in _listings if l.user_id == user_id]


async def claim_listing(listing_id: str, user_id: str) -> CommunityListing | None:
    for listing in _listings:
        if listing.id == listing_id:
            if listing.status != ListingStatus.AVAILABLE:
                return None
            listing.status = ListingStatus.CLAIMED
            listing.claimed_by = user_id
            return listing
    return None


async def delete_listing(listing_id: str, user_id: str) -> bool:
    for i, listing in enumerate(_listings):
        if listing.id == listing_id and listing.user_id == user_id:
            _listings.pop(i)
            return True
    return False
