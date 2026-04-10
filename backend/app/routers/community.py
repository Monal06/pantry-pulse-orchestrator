from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.community import CommunityListingCreate
from app.services import community_service

router = APIRouter(prefix="/community", tags=["community"])

DEFAULT_USER = "demo-user"


@router.get("/listings")
async def get_available_listings(user_id: str = Query(default=DEFAULT_USER)):
    """Get all available community food listings (excluding your own)."""
    listings = await community_service.get_available_listings(exclude_user=user_id)
    return [l.model_dump(mode="json") for l in listings]


@router.get("/my-listings")
async def get_my_listings(user_id: str = Query(default=DEFAULT_USER)):
    """Get your own community listings."""
    listings = await community_service.get_my_listings(user_id)
    return [l.model_dump(mode="json") for l in listings]


@router.post("/listings")
async def create_listing(
    data: CommunityListingCreate,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Post surplus food for the community to claim."""
    listing = await community_service.create_listing(user_id, data)
    return listing.model_dump(mode="json")


@router.post("/listings/{listing_id}/claim")
async def claim_listing(
    listing_id: str,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Claim a community food listing."""
    listing = await community_service.claim_listing(listing_id, user_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not available")
    return listing.model_dump(mode="json")


@router.delete("/listings/{listing_id}")
async def delete_listing(
    listing_id: str,
    user_id: str = Query(default=DEFAULT_USER),
):
    """Remove your own listing."""
    deleted = await community_service.delete_listing(listing_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Listing not found")
    return {"status": "deleted"}
