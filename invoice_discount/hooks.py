# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID
from odoo.api import Environment
from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)

COLUMNS = (
    ("account_move", "subtotal_wo_discount"),
    ("account_move", "discount_amount"),
    ("account_move_line", "subtotal_wo_discount"),
    ("account_move_line", "discount_amount"),
)


def pre_init_hook(cr):
    for table, column in COLUMNS:
        if not column_exists(cr, table, column):
            _logger.info("Create discount column %s in database", column)
            create_column(cr, table, column, "numeric")


def post_init_hook(cr, registry):
    _logger.info("Compute discount columns")
    env = Environment(cr, SUPERUSER_ID, {})

    env.cr.execute("""
        UPDATE account_move_line
        SET subtotal_wo_discount = quantity * price_unit
        WHERE discount > 0.0;
    """)
    env.cr.execute("""
        UPDATE account_move_line
        SET discount_amount = discount * subtotal_wo_discount / 100
        WHERE discount > 0.0;
    """)

    query = """
    select distinct move_id from account_move_line where discount > 0.0;
    """
    cr.execute(query)
    move_ids = cr.fetchall()

    moves = env["account.move"].search([("id", "in", move_ids)])
    moves._compute_discount_amounts()
