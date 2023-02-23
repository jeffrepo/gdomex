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
