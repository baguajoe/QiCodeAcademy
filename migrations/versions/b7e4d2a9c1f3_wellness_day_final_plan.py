"""wellness day: final plan (no sewing; fall prevention & balance; new vendor types)

Revision ID: b7e4d2a9c1f3
Revises: a3c9e2f1b7d4
Create Date: 2026-10-28 23:30:00.000000

Data only (no schema change). Existing rows are renamed to the new keys so they keep their meaning:
    activities           strength_balance   -> fall_prevention_balance
                         painting_sewing    -> painting
                         wellness_education -> resources
                         acupressure        -> (dropped: no longer offered)
    participation_types  arts_crafts        -> painting
    vendor_category      art -> visual_art, books_media -> books, wellness_products -> skincare_wellness,
                         crafts -> other
"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e4d2a9c1f3'
down_revision = 'a3c9e2f1b7d4'
branch_labels = None
depends_on = None

ACTIVITY_UP = {"strength_balance": ["fall_prevention_balance"], "painting_sewing": ["painting"],
               "wellness_education": ["resources"], "acupressure": []}
ACTIVITY_DOWN = {"fall_prevention_balance": ["strength_balance"], "painting": ["painting_sewing"],
                 "resources": ["wellness_education"], "chair_hip_hop": [], "self_massage": [], "sound_healing": []}
TYPE_UP = {"arts_crafts": ["painting"]}
TYPE_DOWN = {"painting": ["arts_crafts"], "sound_healing": ["instructor"], "instructor_chair_yoga": ["instructor"],
             "instructor_chair_hip_hop": ["instructor"], "instructor_meditation": ["instructor"]}
CATEGORY_UP = {"art": "visual_art", "books_media": "books", "wellness_products": "skincare_wellness", "crafts": "other"}
CATEGORY_DOWN = {"visual_art": "art", "books": "books_media", "skincare_wellness": "wellness_products",
                 "jewelry": "jewelry", "clothing": "clothing", "food": "food", "other": "other"}


def _remap(table, column, mapping):
    conn = op.get_bind()
    t = sa.table(table, sa.column("id", sa.Integer), sa.column(column, sa.JSON))
    for row_id, values in conn.execute(sa.select(t.c.id, t.c[column])).all():
        if isinstance(values, str):
            values = json.loads(values)
        out = []
        for v in values or []:
            for new in mapping.get(v, [v]):
                if new not in out:
                    out.append(new)
        if out != (values or []):
            conn.execute(t.update().where(t.c.id == row_id).values({column: out}))


def _remap_category(mapping, default=None):
    """Rename vendor_category values; anything not in the mapping becomes `default` (None = keep)."""
    conn = op.get_bind()
    t = sa.table("wellness_day_partners", sa.column("id", sa.Integer), sa.column("vendor_category", sa.String))
    for row_id, value in conn.execute(sa.select(t.c.id, t.c.vendor_category).where(t.c.vendor_category.isnot(None))).all():
        new = mapping.get(value, default or value)
        if new != value:
            conn.execute(t.update().where(t.c.id == row_id).values(vendor_category=new))


def upgrade():
    _remap("wellness_day_interest", "activities", ACTIVITY_UP)
    _remap("wellness_day_partners", "participation_types", TYPE_UP)
    _remap_category(CATEGORY_UP)


def downgrade():
    _remap("wellness_day_interest", "activities", ACTIVITY_DOWN)
    _remap("wellness_day_partners", "participation_types", TYPE_DOWN)
    _remap_category(CATEGORY_DOWN, default="other")
