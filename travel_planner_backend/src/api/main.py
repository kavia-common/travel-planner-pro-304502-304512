from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.auth import router as auth_router
from src.routers.bookings import router as bookings_router
from src.routers.destinations import router as destinations_router
from src.routers.favorites import router as favorites_router
from src.routers.itinerary import router as itinerary_router
from src.routers.trips import router as trips_router
from src.schemas.common import MessageResponse
from src.storage.db import init_db

openapi_tags = [
    {"name": "health", "description": "Health and metadata endpoints"},
    {"name": "auth", "description": "Local email/password authentication (demo-friendly)"},
    {"name": "trips", "description": "Trip planning and management"},
    {"name": "destinations", "description": "Destinations under trips"},
    {"name": "itinerary", "description": "Itinerary items (calendar-like events)"},
    {"name": "bookings", "description": "Bookings for transport/lodging/etc"},
    {"name": "favorites", "description": "Favorite destinations"},
]

app = FastAPI(
    title="Travel Planner Backend API",
    description=(
        "Backend API for the Travel Planner app: auth, trips, destinations, itinerary items, bookings, and favorites.\n\n"
        "Auth is a minimal local implementation that returns a Bearer token to be used in the Authorization header."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# Allow local frontend in dev (port 3000) plus permissive wildcard as fallback.
# If you want stricter CORS, set BACKEND_CORS_ORIGINS as comma-separated list.
default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    """Initialize database tables on startup."""
    await init_db()


@app.get(
    "/",
    response_model=MessageResponse,
    tags=["health"],
    summary="Health check",
    description="Basic health check endpoint.",
    operation_id="health_check",
)
def health_check() -> MessageResponse:
    """Return a simple health response."""
    return MessageResponse(message="Healthy")


@app.get(
    "/docs/help",
    response_model=MessageResponse,
    tags=["health"],
    summary="API usage help",
    description="Quick notes on how to authenticate and call the API from the frontend.",
    operation_id="docs_help",
)
def docs_help() -> MessageResponse:
    """Provide basic usage help, especially for authentication."""
    return MessageResponse(
        message=(
            "Usage:\n"
            "1) POST /auth/login with {email,password} (demo: demo@example.com / demo123)\n"
            "2) Use header: Authorization: Bearer <access_token>\n"
            "3) Call /trips, /destinations, /itinerary, /bookings, /favorites\n"
        )
    )


# Routers
app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(destinations_router)
app.include_router(itinerary_router)
app.include_router(bookings_router)
app.include_router(favorites_router)
