# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale order line')
    move_line_id = fields.Many2one('stock.move', 'Move line')
    unidad = fields.Float('Unidad')
    largo = fields.Float('Largo')
