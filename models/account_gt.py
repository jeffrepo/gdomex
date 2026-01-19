from odoo import api, fields, models, tools, _
from odoo.modules import get_module_resource
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
import logging

class Liquidacion(models.Model):
    _inherit = "account_gt.liquidacion"

    @api.model
    def create(self, vals):
        
        seq_date = None
        logging.warning('create')
        company_id = self.env.company.id
        logging.warning(company_id)
        if company_id == 1:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_domex', sequence_date=seq_date) or _('New')
        if company_id == 6:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_almex', sequence_date=seq_date) or _('New')
        if company_id == 7:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_recubrimientos', sequence_date=seq_date) or _('New')
        if company_id == 8:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_neira', sequence_date=seq_date) or _('New')
        if company_id == 9:
            logging.warning('es 9')
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_bordalas', sequence_date=seq_date) or _('New')             
        if company_id == 10:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_argentiera', sequence_date=seq_date) or _('New')                  
        if company_id == 11:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_vinyasa', sequence_date=seq_date) or _('New')                  
        if company_id == 12:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_galmex', sequence_date=seq_date) or _('New')
        if company_id == 38:
            vals['name'] = self.env['ir.sequence'].next_by_code(
            'account_gt.liquidacion_aply', sequence_date=seq_date) or _('New') 
        logging.warning('vals')
        logging.warning(vals)
        result = super(Liquidacion, self).create(vals)
        return result

class ResCompany(models.Model):
    _inherit = "res.company"

    ft_cuenta_analitica_ids = fields.Many2many('account.analytic.account',string='Cuenta analitica flete y transporte')
