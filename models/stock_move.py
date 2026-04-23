# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import logging

VALUATION_DICT = {
    'value': 0,
    'quantity': 0,
    'description': False,
}


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

    def _get_value_from_quotation(self, quantity, at_date=None):
        self.ensure_one()

        line = self.purchase_line_id
        if not line or self.product_id != line.product_id:
            return super()._get_value_from_quotation(quantity, at_date=at_date)
        order = line.order_id
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')

        # Precio base de la línea de compra
        price_unit = line.price_unit or 0.0

        # Impuestos
        if line.tax_ids:
            qty_po = line.product_qty or 1.0
            taxes_res = line.tax_ids.with_context(round=False).compute_all(
                price_unit,
                currency=order.currency_id,
                quantity=qty_po,
                product=line.product_id,
                partner=order.partner_id,
            )
            # Si total_void no existe en tu rama, usa total_excluded
            net_total = taxes_res.get('total_void', taxes_res.get('total_excluded', price_unit * qty_po))
            price_unit = float_round(
                net_total / qty_po,
                precision_digits=price_unit_prec,
            )

        # UoM de la línea de compra -> UoM del producto
        if line.product_uom_id and line.product_uom_id != line.product_id.uom_id:
            price_unit *= line.product_uom_id.factor / line.product_id.uom_id.factor

        conversion_date = False
        if order.currency_id != order.company_id.currency_id:
            conversion_date = order.fecha_tipo_cambio or order.date_order or fields.Date.context_today(self)
            price_unit = order.currency_id._convert(
                price_unit,
                order.company_id.currency_id,
                order.company_id,
                conversion_date,
                round=False,
            )

        return {
            'value': price_unit * quantity,
            'quantity': quantity,
            'description': _(
                "Valued from purchase order %(po)s%(fx)s",
                po=order.name,
                fx=conversion_date and _(" using exchange date %(date)s", date=conversion_date) or "",
            ),
        }

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    mrp_id = fields.Many2one('mrp.production','Fabricacion')
