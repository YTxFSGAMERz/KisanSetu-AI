"""Analytics routes — Government Admin and Officer dashboards."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.database.session import get_db
from app.models.user import UserRole
from app.models.centre import ProcurementCentre
from app.models.farmer import Farmer
from app.models.booking import Booking, BookingStatus
from app.models.queue_token import QueueToken, TokenStatus
from app.models.procurement import Procurement, ProcurementStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.analytics import (
    AdminDashboardResponse,
    CentreAnalytics,
    OfficerDashboardResponse,
)
from app.services.recommendation_engine import compute_congestion_score

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/admin/dashboard", response_model=AdminDashboardResponse)
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.GOVERNMENT_ADMIN, UserRole.CENTRE_ADMIN)),
):
    today = date.today()

    # Total active centres
    centres_result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.is_active == True)
    )
    centres = centres_result.scalars().all()

    # Total farmers
    farmers_count_result = await db.execute(select(func.count(Farmer.id)))
    total_farmers = farmers_count_result.scalar() or 0

    # Farmers served today
    served_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.status == TokenStatus.COMPLETED,
            func.date(QueueToken.completed_at) == today,
        )
    )
    served_today = served_result.scalar() or 0

    # Avg waiting minutes (estimate from completed tokens)
    avg_wait_result = await db.execute(
        select(func.avg(QueueToken.estimated_wait_minutes)).where(
            QueueToken.status == TokenStatus.COMPLETED
        )
    )
    avg_wait = float(avg_wait_result.scalar() or 20.0)

    # Total procurement quantity (quintals)
    total_qty_result = await db.execute(
        select(func.sum(Procurement.accepted_quantity)).where(
            Procurement.status == ProcurementStatus.COMPLETED
        )
    )
    total_qty = float(total_qty_result.scalar() or 0.0)

    # Payment completion rate
    total_pay_result = await db.execute(select(func.count(Payment.id)))
    completed_pay_result = await db.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.COMPLETED)
    )
    total_payments = total_pay_result.scalar() or 1
    completed_payments = completed_pay_result.scalar() or 0
    pay_rate = round((completed_payments / max(total_payments, 1)) * 100, 1)

    # Per-centre analytics
    centre_analytics = []
    for centre in centres:
        completed_today_result = await db.execute(
            select(func.count(QueueToken.id)).where(
                QueueToken.centre_id == centre.id,
                QueueToken.status == TokenStatus.COMPLETED,
                func.date(QueueToken.completed_at) == today,
            )
        )
        no_show_result = await db.execute(
            select(func.count(QueueToken.id)).where(
                QueueToken.centre_id == centre.id,
                QueueToken.status == TokenStatus.NO_SHOW,
                func.date(QueueToken.created_at) == today,
            )
        )
        waiting_result = await db.execute(
            select(func.count(QueueToken.id)).where(
                QueueToken.centre_id == centre.id,
                QueueToken.status == TokenStatus.WAITING,
            )
        )
        qty_result = await db.execute(
            select(func.sum(Procurement.accepted_quantity))
            .join(Booking, Procurement.booking_id == Booking.id)
            .where(
                Booking.centre_id == centre.id,
                Procurement.status == ProcurementStatus.COMPLETED,
            )
        )
        amt_result = await db.execute(
            select(func.sum(Procurement.procurement_amount))
            .join(Booking, Procurement.booking_id == Booking.id)
            .where(
                Booking.centre_id == centre.id,
                Procurement.status == ProcurementStatus.COMPLETED,
            )
        )
        centre_waiting = waiting_result.scalar() or 0
        congestion = compute_congestion_score(
            booked_count=centre.daily_capacity // 2,
            slot_capacity=centre.daily_capacity,
            active_queue_length=centre_waiting,
            daily_target=centre.daily_capacity,
            avg_processing_minutes=centre.avg_processing_minutes,
        )
        centre_analytics.append(
            CentreAnalytics(
                centre_id=centre.id,
                centre_name=centre.name,
                congestion_score=congestion,
                farmers_today=completed_today_result.scalar() or 0,
                completed_today=completed_today_result.scalar() or 0,
                no_shows_today=no_show_result.scalar() or 0,
                avg_processing_minutes=centre.avg_processing_minutes,
                total_quantity_kg=float(qty_result.scalar() or 0.0),
                total_amount=float(amt_result.scalar() or 0.0),
            )
        )

    # Daily volume chart (last 7 days)
    daily_chart = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_qty_result = await db.execute(
            select(func.sum(Procurement.accepted_quantity), func.count(Procurement.id)).where(
                Procurement.status == ProcurementStatus.COMPLETED,
                func.date(Procurement.completed_at) == d,
            )
        )
        row = day_qty_result.one()
        daily_chart.append({
            "date": str(d),
            "quantity": float(row[0] or 0),
            "count": int(row[1] or 0),
        })

    return AdminDashboardResponse(
        total_active_centres=len(centres),
        total_registered_farmers=total_farmers,
        farmers_served_today=served_today,
        avg_waiting_minutes=round(avg_wait, 1),
        total_procurement_quintals=total_qty,
        payment_completion_rate=pay_rate,
        centres=centre_analytics,
        daily_volume_chart=daily_chart,
        no_show_rate=round(
            (sum(c.no_shows_today for c in centre_analytics) / max(served_today, 1)) * 100, 1
        ),
    )


@router.get("/officer/dashboard", response_model=OfficerDashboardResponse)
async def officer_dashboard(
    centre_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(UserRole.PROCUREMENT_OFFICER, UserRole.CENTRE_ADMIN, UserRole.GOVERNMENT_ADMIN)),
):
    today = date.today()

    centre_result = await db.execute(
        select(ProcurementCentre).where(ProcurementCentre.id == centre_id)
    )
    centre = centre_result.scalar_one_or_none()

    expected_result = await db.execute(
        select(func.count(Booking.id)).where(
            Booking.centre_id == centre_id,
            func.date(Booking.created_at) <= today,
            Booking.booking_status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        )
    )
    processing_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status.in_([TokenStatus.CALLED, TokenStatus.PROCESSING]),
        )
    )
    waiting_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id, QueueToken.status == TokenStatus.WAITING
        )
    )
    completed_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.COMPLETED,
            func.date(QueueToken.completed_at) == today,
        )
    )
    no_show_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            QueueToken.centre_id == centre_id,
            QueueToken.status == TokenStatus.NO_SHOW,
            func.date(QueueToken.created_at) == today,
        )
    )

    waiting = waiting_result.scalar() or 0
    congestion = compute_congestion_score(
        booked_count=centre.daily_capacity // 2 if centre else 50,
        slot_capacity=centre.daily_capacity if centre else 100,
        active_queue_length=waiting,
        daily_target=centre.daily_capacity if centre else 100,
        avg_processing_minutes=centre.avg_processing_minutes if centre else 20.0,
    )

    return OfficerDashboardResponse(
        centre_id=centre_id,
        centre_name=centre.name if centre else "Unknown Centre",
        expected_today=expected_result.scalar() or 0,
        currently_processing=processing_result.scalar() or 0,
        waiting=waiting,
        completed=completed_result.scalar() or 0,
        no_shows=no_show_result.scalar() or 0,
        avg_processing_minutes=centre.avg_processing_minutes if centre else 20.0,
        congestion_score=congestion,
    )
