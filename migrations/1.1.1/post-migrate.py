from odoo import SUPERUSER_ID, api

SEQUENCE_CODES = ("cs.psychology.session", "cs.initial.assessment", "cs.family.call")


def migrate(cr, version):
    """Secuencias compartidas: con compañía, next_by_code no las encuentra en otras compañías."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.sequence"].search([("code", "in", SEQUENCE_CODES)]).write({"company_id": False})
