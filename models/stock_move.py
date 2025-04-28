# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

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

    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if not self.origin_returned_move_id and self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line._prepare_compute_all_values()['price_unit']
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=qty, product=self.product_id)['total_void']
                price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36

                if order.fecha_tipo_cambio:
                    price_unit = order.currency_id._convert(
                        price_unit, order.company_id.currency_id, order.company_id, order.fecha_tipo_cambio, round=False)
                    self.price_unit = price_unit
                else:
                    price_unit = order.currency_id._convert(
                        price_unit, order.company_id.currency_id, order.company_id, fields.Date.context_today(self), round=False)
            return price_unit
        return super(StockMove, self)._get_price_unit()

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    mrp_id = fields.Many2one('mrp.production','Fabricacion')
