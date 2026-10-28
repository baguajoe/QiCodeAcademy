"""wellness day: acupuncture, marketplace vendors, senior makers

Revision ID: a3c9e2f1b7d4
Revises: 657cdfcbb84e
Create Date: 2026-10-28 14:00:00.000000

- Interest list: wants_to_sell / sell_items / needs_table (Senior Makers Market).
- Partners: vendor_category / vendor_products / vendor_price_range, and the four new agreements.
- Data: split the old combined keys into the new ones so existing rows keep their meaning:
    activities           massage_acupressure -> chair_massage + acupressure
    participation_types  practitioner        -> practitioner_bodywork (staff can refine to massage/acupuncture)
                         food                -> food_vendor
"""
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3c9e2f1b7d4'
down_revision = '657cdfcbb84e'
branch_labels = None
depends_on = None

ACTIVITY_UP = {"massage_acupressure": ["chair_massage", "acupressure"]}
ACTIVITY_DOWN = {"chair_massage": ["massage_acupressure"], "acupressure": ["massage_acupressure"],
                 "acupuncture": ["massage_acupressure"], "marketplace": []}
TYPE_UP = {"practitioner": ["practitioner_bodywork"], "food": ["food_vendor"]}
TYPE_DOWN = {"practitioner_massage": ["practitioner"], "practitioner_acupuncture": ["practitioner"],
             "practitioner_bodywork": ["practitioner"], "food_vendor": ["food"], "vendor": ["arts_crafts"]}


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


def upgrade():
    with op.batch_alter_table('wellness_day_interest', schema=None) as batch_op:
        batch_op.add_column(sa.Column('wants_to_sell', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('sell_items', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('needs_table', sa.String(length=3), nullable=True))
        batch_op.create_index(batch_op.f('ix_wellness_day_interest_wants_to_sell'), ['wants_to_sell'], unique=False)

    with op.batch_alter_table('wellness_day_partners', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vendor_category', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('vendor_products', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('vendor_price_range', sa.String(length=100), nullable=True))
        for col in ('agrees_respectful', 'agrees_permits', 'agrees_restricted_products'):
            batch_op.add_column(sa.Column(col, sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index(batch_op.f('ix_wellness_day_partners_vendor_category'), ['vendor_category'], unique=False)

    _remap('wellness_day_interest', 'activities', ACTIVITY_UP)
    _remap('wellness_day_partners', 'participation_types', TYPE_UP)


def downgrade():
    _remap('wellness_day_partners', 'participation_types', TYPE_DOWN)
    _remap('wellness_day_interest', 'activities', ACTIVITY_DOWN)

    with op.batch_alter_table('wellness_day_partners', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wellness_day_partners_vendor_category'))
        for col in ('agrees_restricted_products', 'agrees_permits', 'agrees_respectful',
                    'vendor_price_range', 'vendor_products', 'vendor_category'):
            batch_op.drop_column(col)

    with op.batch_alter_table('wellness_day_interest', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wellness_day_interest_wants_to_sell'))
        for col in ('needs_table', 'sell_items', 'wants_to_sell'):
            batch_op.drop_column(col)
