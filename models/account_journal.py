# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    cuenta_default = fields.Boolean("Utilizar cuenta por default")
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta analítica",
        check_company=True,
        ondelete="restrict",
        help=(
            "Cuenta analítica que se asignará al 100 % a las nuevas "
            "líneas de facturas de cliente y proveedor de este diario."
        ),
    )
