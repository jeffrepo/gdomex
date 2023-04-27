# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

class AccountMove(models.Model):
    _inherit = "account.move"
    
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