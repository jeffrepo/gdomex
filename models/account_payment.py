# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

class AccountPayment(models.Model):
    _inherit = "account.payment"

    no_negociable = fields.Boolean(string='No negociable',default=True)
    nombre_impreso = fields.Char(string='Nombre impreso')
    cuenta_transitoria_id = fields.Many2one('account.account', 'Cuenta transitoria')

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        if self.cuenta_transitoria_id:
            self.destination_account_id = self.cuenta_transitoria_id.id

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('move_type')
    def _compute_invoice_filter_type_domain(self):
        res = super(AccountMove, self)._compute_invoice_filter_type_domain()
        logging.warning(res)
