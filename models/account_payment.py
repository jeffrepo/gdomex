# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    no_negociable = fields.Boolean(string='No negociable',default=False)
    nombre_impreso = fields.Char(string='Nombre impreso')

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('move_type')
    def _compute_invoice_filter_type_domain(self):
        res = super(AccountMove, self)._compute_invoice_filter_type_domain()
        logging.warning(res)
