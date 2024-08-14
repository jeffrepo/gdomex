# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

class AccountMove(models.Model):
    _inherit = "account.move"
    
    otro_comentario = fields.Char('Otro comentario')
    
    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            company_id = m.company_id.id or self.env.company.id
            if m.move_type != 'entry':
                journal_type = m.invoice_filter_type_domain or 'general'
                domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            else:
                journal_type = m.invoice_filter_type_domain or ['general','cash','bank']
                domain = [('company_id', '=', company_id), ('type', 'in', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_account(self):
        res = super()._get_computed_account()
        if self.move_id.journal_id.cuenta_default and self.move_id.is_sale_document(include_receipts=True):
            return self.move_id.journal_id.default_account_id
        else:
            return res