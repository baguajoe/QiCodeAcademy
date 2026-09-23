"""Donations: Stripe Checkout session creation + signed webhook."""
import json
from decimal import Decimal

import stripe
from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import select

from ..extensions import db, limiter
from ..models import Donation, utcnow
from ..schemas import DonationCheckoutSchema
from ..services import notifications
from ..utils import APIError, get_json, honeypot, load

bp = Blueprint("donations", __name__, url_prefix="/api")

DESIGNATION_LABELS = {"youth": "Youth programs", "senior": "Senior programs",
                      "research": "Research", "general": "Where it's needed most"}


def _with_session_placeholder(url):
    if "{CHECKOUT_SESSION_ID}" in url:
        return url
    return f"{url}{'&' if '?' in url else '?'}session_id={{CHECKOUT_SESSION_ID}}"


@bp.post("/donations/create-checkout-session")
@limiter.limit(lambda: current_app.config["RATELIMIT_DONATIONS"])
@honeypot({"url": None, "id": None}, status=200)
def create_checkout_session():
    cfg = current_app.config
    if not (cfg["STRIPE_SECRET_KEY"] and cfg["STRIPE_SUCCESS_URL"] and cfg["STRIPE_CANCEL_URL"]):
        raise APIError("Online donations aren't available yet. Please check back soon.", 503,
                       "donations_unavailable")

    data = load(DonationCheckoutSchema(), get_json())
    cents = int((Decimal(data["amount"]) * 100).to_integral_value())
    if not cfg["DONATION_MIN_CENTS"] <= cents <= cfg["DONATION_MAX_CENTS"]:
        lo, hi = cfg["DONATION_MIN_CENTS"] / 100, cfg["DONATION_MAX_CENTS"] / 100
        raise APIError(f"Please enter an amount between ${lo:,.2f} and ${hi:,.2f}.", 400,
                       "validation_error", {"amount": [f"Amount must be ${lo:,.0f}–${hi:,.0f}."]})

    recurring, designation = data["recurring"], data["designation"]
    donation = Donation(amount_cents=cents, recurring=recurring, designation=designation,
                        donor_name=data.get("donor_name"), donor_email=data.get("donor_email"),
                        currency=cfg["STRIPE_CURRENCY"], status="pending")
    db.session.add(donation)
    db.session.flush()  # get an id for metadata

    metadata = {"donation_id": str(donation.id), "designation": designation,
                "recurring": "true" if recurring else "false"}
    label = DESIGNATION_LABELS[designation]
    description = f"{'Monthly donation' if recurring else 'Donation'} to {cfg['ORG_LEGAL_NAME']} — {label}"
    price_data = {"currency": cfg["STRIPE_CURRENCY"], "unit_amount": cents,
                  "product_data": {"name": description}}
    params = {
        "success_url": _with_session_placeholder(cfg["STRIPE_SUCCESS_URL"]),
        "cancel_url": cfg["STRIPE_CANCEL_URL"],
        "client_reference_id": str(donation.id),
        "metadata": metadata,
        "line_items": [{"price_data": price_data, "quantity": 1}],
    }
    if data.get("donor_email"):
        params["customer_email"] = data["donor_email"]
    if recurring:
        price_data["recurring"] = {"interval": "month"}
        params["mode"] = "subscription"
        params["subscription_data"] = {"metadata": metadata, "description": description}
    else:
        params["mode"] = "payment"
        params["submit_type"] = "donate"
        params["payment_intent_data"] = {"metadata": metadata, "description": description}

    try:
        session = stripe.checkout.Session.create(
            api_key=cfg["STRIPE_SECRET_KEY"], idempotency_key=f"qca-donation-{donation.id}", **params)
    except stripe.StripeError as exc:
        db.session.rollback()
        current_app.logger.error("Stripe checkout error: %s", exc)
        raise APIError("We couldn't start the payment. Please try again in a moment.", 502,
                       "payment_provider_error")

    donation.stripe_session_id = session.id
    db.session.commit()
    return jsonify({"url": session.url, "id": session.id})


# ---------------------------------------------------------------------------
# Webhook
# ---------------------------------------------------------------------------
@bp.post("/stripe/webhook")
def stripe_webhook():
    secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    if not secret:
        raise APIError("Webhook not configured.", 503, "webhook_unavailable")
    payload = request.get_data()
    try:
        stripe.Webhook.construct_event(payload, request.headers.get("Stripe-Signature", ""), secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise APIError("Invalid signature.", 400, "invalid_signature")

    event = json.loads(payload)  # verified; use plain dicts from here on
    handler = HANDLERS.get(event.get("type"))
    if handler:
        handler(event["data"]["object"])
        db.session.commit()
    return jsonify({"received": True})


def _find_by_session(session):
    donation = db.session.scalar(select(Donation).where(Donation.stripe_session_id == session["id"]))
    if donation is None:
        donation_id = (session.get("metadata") or {}).get("donation_id") or session.get("client_reference_id")
        if donation_id and str(donation_id).isdigit():
            donation = db.session.get(Donation, int(donation_id))
            if donation and donation.stripe_session_id not in (None, session["id"]):
                donation = None
    return donation


def _send_receipt_once(donation):
    if donation.status == "completed" and donation.receipt_sent_at is None and donation.donor_email:
        donation.receipt_sent_at = utcnow()
        db.session.commit()
        notifications.donation_thank_you(donation)


def _on_session_completed(session):
    donation = _find_by_session(session)
    if donation is None:
        current_app.logger.warning("Stripe session %s has no matching donation", session.get("id"))
        return
    details = session.get("customer_details") or {}
    donation.stripe_session_id = session["id"]
    donation.donor_email = donation.donor_email or details.get("email")
    donation.donor_name = donation.donor_name or details.get("name")
    donation.stripe_customer_id = session.get("customer") or donation.stripe_customer_id
    donation.stripe_payment_intent_id = session.get("payment_intent") or donation.stripe_payment_intent_id
    donation.stripe_subscription_id = session.get("subscription") or donation.stripe_subscription_id
    if session.get("amount_total") is not None:
        donation.amount_cents = session["amount_total"]
    if donation.recurring:
        donation.subscription_status = donation.subscription_status or "active"
    if session.get("payment_status") in ("paid", "no_payment_required"):
        donation.status = "completed"
    _send_receipt_once(donation)


def _on_async_succeeded(session):
    donation = _find_by_session(session)
    if donation:
        donation.status = "completed"
        _send_receipt_once(donation)


def _on_async_failed(session):
    donation = _find_by_session(session)
    if donation and donation.status == "pending":
        donation.status = "failed"


def _on_session_expired(session):
    donation = _find_by_session(session)
    if donation and donation.status == "pending":
        donation.status = "expired"


def _invoice_subscription_id(invoice):
    # Older API versions: invoice.subscription; 2025+ ("basil"): invoice.parent.subscription_details.
    sub = invoice.get("subscription")
    if not sub:
        sub = (((invoice.get("parent") or {}).get("subscription_details")) or {}).get("subscription")
    return sub.get("id") if isinstance(sub, dict) else sub


def _on_invoice_paid(invoice):
    """Monthly renewals: record each paid cycle as its own completed Donation."""
    if invoice.get("billing_reason") == "subscription_create":
        return  # first payment is recorded via checkout.session.completed
    sub_id = _invoice_subscription_id(invoice)
    if not sub_id or not invoice.get("id"):
        return
    if db.session.scalar(select(Donation).where(Donation.stripe_invoice_id == invoice["id"])):
        return  # already recorded (webhook retry)
    original = db.session.scalar(
        select(Donation).where(Donation.stripe_subscription_id == sub_id,
                               Donation.stripe_session_id.is_not(None)))
    if original is None:
        current_app.logger.warning("Renewal invoice %s for unknown subscription %s", invoice["id"], sub_id)
        return
    renewal = Donation(
        stripe_invoice_id=invoice["id"], stripe_subscription_id=sub_id,
        stripe_customer_id=invoice.get("customer") or original.stripe_customer_id,
        amount_cents=invoice.get("amount_paid") or original.amount_cents,
        currency=invoice.get("currency") or original.currency, recurring=True,
        designation=original.designation, donor_name=original.donor_name,
        donor_email=original.donor_email or invoice.get("customer_email"), status="completed")
    db.session.add(renewal)
    db.session.flush()
    _send_receipt_once(renewal)


def _on_subscription_changed(subscription):
    for donation in db.session.scalars(
            select(Donation).where(Donation.stripe_subscription_id == subscription.get("id"),
                                   Donation.stripe_session_id.is_not(None))):
        donation.subscription_status = subscription.get("status")


def _on_charge_refunded(charge):
    if not charge.get("refunded") or not charge.get("payment_intent"):
        return  # partial refunds are left for manual review
    for donation in db.session.scalars(
            select(Donation).where(Donation.stripe_payment_intent_id == charge["payment_intent"])):
        donation.status = "refunded"


HANDLERS = {
    "checkout.session.completed": _on_session_completed,
    "checkout.session.async_payment_succeeded": _on_async_succeeded,
    "checkout.session.async_payment_failed": _on_async_failed,
    "checkout.session.expired": _on_session_expired,
    "invoice.paid": _on_invoice_paid,
    "customer.subscription.updated": _on_subscription_changed,
    "customer.subscription.deleted": _on_subscription_changed,
    "charge.refunded": _on_charge_refunded,
}
