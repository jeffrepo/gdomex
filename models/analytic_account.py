from odoo import models, fields, api, _

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    picking_line_id = fields.Many2one('stock.move', string='Ref stock move')
