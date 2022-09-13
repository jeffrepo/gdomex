# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    por_facturar = fields.Monetary('Por facturar', compute='_new_total_invoice', store=True)

    @api.depends('order_line.price_total', 'invoice_ids', 'invoice_count')
    def _new_total_invoice(self):
        for order in self:
            order.por_facturar = order.amount_total
            if order.invoice_ids:
                total_facturas = 0
                for factura in order.invoice_ids:
                    if factura.state == 'posted':
                        if factura.amount_total_signed > 0 and order.amount_total > 0:

                            total_facturas += factura.amount_total_signed
                            order.por_facturar = order.amount_total - total_facturas

                if order.por_facturar == 0:
                    order.invoice_status = 'invoiced'
