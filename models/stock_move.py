# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    largo_gdomex = fields.Float(string='Largo')
    ancho_gdomex = fields.Float(string='Ancho')
    color_gdomex = fields.Char(string='Color')
    calibre_gdomex = fields.Char(string='Calibre')
    desarrollo_gdomex = fields.Char(string='Desarrollo')
    unidad = fields.Integer('Unidad')
    mrp_id = fields.Many2one('mrp.production','Fabricacion')

    @api.onchange('unidad','largo_gdomex')
    def _onchange_domex_unidad(self):
        if self.product_id.uom_id.name == "m" and (self.unidad > 0 or self.largo_gdomex > 0):
            self.product_uom_qty = self.unidad * self.largo_gdomex


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    mrp_id = fields.Many2one('mrp.production','Fabricacion')
