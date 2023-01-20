# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    por_facturar = fields.Monetary('Por facturar', compute='_new_total_invoice', store=True)
    proyecto = fields.Char('Proyecto')
    atencion = fields.Many2one('res.partner', string='Atención')
    supplier = fields.Many2one('res.partner', string='Supplier')
    bill_to = fields.Many2one('res.partner', string='Bill to')
    consigned_to = fields.Many2one('res.partner', string='Consigned to')
    send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    marks = fields.Text(string="Marks")
    insurance = fields.Char('Insurance')
    delivery = fields.Char('Delivery')
    comision = fields.Float('Comision de ventas')
    lugar_entrega = fields.Char('Lugar de entrega')
    tiempo_estimado_entrega = fields.Char('Tiempo estimado de entrega')
    medidas = fields.Char('De acuerdo a')
    oferta_por = fields.Char("Oferta por")
    no_incluyen = fields.Text("Precios no incluyen")
    incluyen = fields.Char("Precios incluyen")
    tiempo_instalacion = fields.Char("Tiempo de instalación")

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

    # # @api.multi
    def recalcular_totales(self):
        for order in self:
            for line in order.order_line:
                line.price_unit = line.price_unit * line.largo
        return True
