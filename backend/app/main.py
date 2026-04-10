from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    inventory, analyze, meals, shopping,
    waste, profile, community, household,
    recipes, notifications,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="FreshSave API",
    description="AI-powered food waste reduction. Track inventory, get freshness scores, meal suggestions, smart shopping lists, community sharing, and more.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(meals.router, prefix="/api")
app.include_router(shopping.router, prefix="/api")
app.include_router(waste.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(household.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "freshsave-api"}
