"""Main API router — registers all sub-routers."""
from fastapi import APIRouter

from app.api.routes import (
    auth,
    farmers,
    centres,
    slots,
    bookings,
    queue,
    procurements,
    payments,
    notifications,
    analytics,
    websocket,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(farmers.router)
api_router.include_router(centres.router)
api_router.include_router(slots.router)
api_router.include_router(bookings.router)
api_router.include_router(queue.router)
api_router.include_router(procurements.router)
api_router.include_router(payments.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)
api_router.include_router(websocket.router)
