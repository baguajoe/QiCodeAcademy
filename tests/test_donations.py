import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest import mock

import pytest
import stripe

from api.models import Donation

SECRET = "whsec_test_dummy"


@pytest.fixture
def fake_stripe():
    with mock.patch("stripe.checkout.Session.create") as create:
        create.return_value = SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.com/c/pay/cs_test_123")
        yield create


def _post_event(client, event_type, obj, secret=SECRET):
    payload = json.dumps({"id": f"evt_{time.time_ns()}", "object": "event", "type": event_type,
                          "data": {"object": obj}})
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    return client.post("/api/stripe/webhook", data=payload, content_type="application/json",
                       headers={"Stripe-Signature": f"t={ts},v1={sig}"})


# --- Checkout ----------------------------------------------------------------
def test_one_time_checkout(client, db, fake_stripe):
    res = client.post("/api/donations/create-checkout-session",
                      json={"amount": "25", "designation": "youth", "donor_email": "d@example.org"})
    assert res.status_code == 200, res.get_json()
    assert res.get_json() == {"url": "https://checkout.stripe.com/c/pay/cs_test_123", "id": "cs_test_123"}

    kwargs = fake_stripe.call_args.kwargs
    assert kwargs["api_key"] == "sk_test_dummy"
    assert kwargs["mode"] == "payment" and kwargs["submit_type"] == "donate"
    assert kwargs["line_items"][0]["price_data"]["unit_amount"] == 2500
    assert "recurring" not in kwargs["line_items"][0]["price_data"]
    assert kwargs["success_url"] == "http://localhost:3001/donate/thank-you?session_id={CHECKOUT_SESSION_ID}"
    assert kwargs["cancel_url"] == "http://localhost:3001/donate/cancelled"
    assert kwargs["customer_email"] == "d@example.org"
    assert kwargs["metadata"]["designation"] == "youth"

    d = db.session.query(Donation).one()
    assert (d.stripe_session_id, d.amount_cents, d.status, d.recurring) == ("cs_test_123", 2500, "pending", False)


def test_monthly_checkout_uses_subscription_price_data(client, db, fake_stripe):
    res = client.post("/api/donations/create-checkout-session",
                      json={"amount": 10.5, "recurring": True, "designation": "research"})
    assert res.status_code == 200
    kwargs = fake_stripe.call_args.kwargs
    assert kwargs["mode"] == "subscription"
    price = kwargs["line_items"][0]["price_data"]
    assert price["recurring"] == {"interval": "month"} and price["unit_amount"] == 1050
    assert kwargs["subscription_data"]["metadata"]["recurring"] == "true"
    assert "submit_type" not in kwargs and "customer_email" not in kwargs
    assert db.session.query(Donation).one().recurring is True


@pytest.mark.parametrize("payload", [
    {"amount": "0.50"}, {"amount": "-5"}, {"amount": "abc"}, {}, {"amount": "1000000"},
    {"amount": "10", "designation": "cats"},
])
def test_checkout_validation(client, fake_stripe, payload):
    assert client.post("/api/donations/create-checkout-session", json=payload).status_code == 400
    fake_stripe.assert_not_called()


def test_checkout_honeypot(client, db, fake_stripe):
    res = client.post("/api/donations/create-checkout-session", json={"amount": "20", "website": "x"})
    assert res.status_code == 200 and res.get_json()["url"] is None
    fake_stripe.assert_not_called()
    assert db.session.query(Donation).count() == 0


def test_checkout_not_configured(app, client):
    app.config["STRIPE_SECRET_KEY"] = ""
    assert client.post("/api/donations/create-checkout-session", json={"amount": "20"}).status_code == 503


def test_checkout_stripe_error(client, db):
    with mock.patch("stripe.checkout.Session.create", side_effect=stripe.APIConnectionError("down")):
        res = client.post("/api/donations/create-checkout-session", json={"amount": "20"})
    assert res.status_code == 502
    assert db.session.query(Donation).count() == 0


# --- Webhook -----------------------------------------------------------------
def test_webhook_rejects_bad_signature(client):
    assert _post_event(client, "checkout.session.completed", {"id": "cs_x"}, secret="whsec_wrong").status_code == 400
    assert client.post("/api/stripe/webhook", data="{}", content_type="application/json").status_code == 400


def _pending(db, **kw):
    d = Donation(amount_cents=2500, designation="youth", status="pending",
                 stripe_session_id="cs_test_123", **kw)
    db.session.add(d)
    db.session.commit()
    return d


def test_webhook_completes_one_time_donation_and_sends_receipt(client, db, outbox):
    d = _pending(db)
    session = {"id": "cs_test_123", "object": "checkout.session", "payment_status": "paid",
               "amount_total": 2500, "payment_intent": "pi_1", "customer": "cus_1",
               "customer_details": {"email": "donor@example.org", "name": "Dee Donor"},
               "metadata": {"donation_id": str(d.id)}}
    assert _post_event(client, "checkout.session.completed", session).status_code == 200
    db.session.refresh(d)
    assert (d.status, d.donor_email, d.donor_name, d.stripe_payment_intent_id) == (
        "completed", "donor@example.org", "Dee Donor", "pi_1")
    assert d.receipt_sent_at is not None
    assert len(outbox) == 1 and outbox[0].to == ["donor@example.org"]

    # Retried webhook: idempotent, no second receipt
    _post_event(client, "checkout.session.completed", session)
    assert len(outbox) == 1

    # Refund
    _post_event(client, "charge.refunded", {"id": "ch_1", "refunded": True, "payment_intent": "pi_1"})
    db.session.refresh(d)
    assert d.status == "refunded"


def test_webhook_async_and_expired(client, db, outbox):
    d = _pending(db)
    _post_event(client, "checkout.session.completed", {"id": "cs_test_123", "payment_status": "unpaid"})
    db.session.refresh(d)
    assert d.status == "pending" and outbox == []
    _post_event(client, "checkout.session.async_payment_failed", {"id": "cs_test_123"})
    db.session.refresh(d)
    assert d.status == "failed"

    d2 = Donation(amount_cents=1000, status="pending", stripe_session_id="cs_exp")
    db.session.add(d2)
    db.session.commit()
    _post_event(client, "checkout.session.expired", {"id": "cs_exp"})
    db.session.refresh(d2)
    assert d2.status == "expired"


def test_webhook_subscription_lifecycle(client, db, outbox):
    d = _pending(db, recurring=True, donor_email="m@example.org")
    _post_event(client, "checkout.session.completed", {
        "id": "cs_test_123", "payment_status": "paid", "amount_total": 2500,
        "subscription": "sub_1", "customer": "cus_1", "mode": "subscription"})
    db.session.refresh(d)
    assert (d.status, d.stripe_subscription_id, d.subscription_status) == ("completed", "sub_1", "active")

    # First invoice is ignored (already recorded by the session)
    _post_event(client, "invoice.paid", {"id": "in_0", "billing_reason": "subscription_create",
                                         "subscription": "sub_1", "amount_paid": 2500})
    assert db.session.query(Donation).count() == 1

    # Renewal (new API shape) creates a new completed donation, once
    renewal = {"id": "in_1", "billing_reason": "subscription_cycle", "amount_paid": 2500,
               "customer": "cus_1", "currency": "usd",
               "parent": {"subscription_details": {"subscription": "sub_1"}}}
    _post_event(client, "invoice.paid", renewal)
    _post_event(client, "invoice.paid", renewal)
    rows = db.session.query(Donation).order_by(Donation.id).all()
    assert len(rows) == 2
    assert (rows[1].stripe_invoice_id, rows[1].status, rows[1].designation) == ("in_1", "completed", "youth")
    assert len(outbox) == 2  # initial + renewal receipts

    _post_event(client, "customer.subscription.deleted", {"id": "sub_1", "status": "canceled"})
    db.session.refresh(d)
    assert d.subscription_status == "canceled"


def test_webhook_unknown_event_ok(client):
    assert _post_event(client, "customer.created", {"id": "cus_1"}).status_code == 200


def test_webhook_not_configured(app, client):
    app.config["STRIPE_WEBHOOK_SECRET"] = ""
    assert _post_event(client, "checkout.session.completed", {"id": "x"}).status_code == 503
