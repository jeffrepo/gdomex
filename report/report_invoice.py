# -*- coding: utf-8 -*-

from odoo import api, models
import re

class ReportAbstractInvoice(models.AbstractModel):
    _name = 'gdomex-1.abstract.reporte_invoice'

    nombre_reporte = ''

    def total_linea(self, l):
        currency = l.invoice_id and l.invoice_id.currency_id or None
        price_unit = l.price_unit * (1 - (l.discount or 0.0) / 100.0)
        taxes = l.invoice_line_tax_ids.compute_all(price_unit, currency, l.quantity, l.product_id, l.invoice_id.partner_id)
        price_total = taxes['total_included']
        timbre = 0
        for tax in taxes['taxes']:
            if tax['name'] == 'Timbre de Prensa Ventas':
                price_total -= tax['amount']
        return price_total

    def impuesto_impresos(self, o):
        impuestos = []
        for tax in o.tax_line_ids:
            if tax.name == 'Timbre de Prensa Ventas':
                impuestos.append({'nombre': 'Timbre de Prensa', 'valor': tax.amount})
        return impuestos

    def total_descuento(self, o):
        t = 0
        for l in o.invoice_line_ids:
            t += ( l.price_unit * l.discount/100 ) * l.quantity
        return t

    def anio(self, o):
        partes = o.date_invoice.split('-')
        if len(partes) > 0:
            return partes[0]
        else:
            return ''

    def mes(self, o):
        partes = o.date_invoice.split('-')
        if len(partes) > 1:
            return partes[1]
        else:
            return ''

    def dia(self, o):
        partes = o.date_invoice.split('-')
        if len(partes) > 2:
            return partes[2]
        else:
            return ''

    def producto(self, nombre):
        return re.sub(r'\[\w+\] ', '', nombre)

    @api.model
    def render_html(self, docids, data=None):
        self.model = 'account.invoice'
        docs = self.env[self.model].browse(docids)

        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'docs': docs,
            'a_letras': odoo.addons.l10n_gt_extra.a_letras,
            'total_descuento': self.total_descuento,
            'anio': self.anio,
            'dia': self.dia,
            'mes': self.mes,
            'producto': self.producto,
            'total_linea': self.total_linea,
            'impuesto_impresos': self.impuesto_impresos,
        }
        return self.env['report'].render(self.nombre_reporte, docargs)

class ReportInvoice1(models.AbstractModel):
    _name = 'report.domex.reporte_invoice1'
    _inherit = 'domex.abstract.reporte_invoice'

    nombre_reporte = 'domex.reporte_invoice1'

class ReportInvoice2(models.AbstractModel):
    _name = 'report.domex.reporte_invoice2'
    _inherit = 'domex.abstract.reporte_invoice'

    nombre_reporte = 'domex.reporte_invoice2'

class ReportInvoice3(models.AbstractModel):
    _name = 'report.domex.reporte_invoice3'
    _inherit = 'domex.abstract.reporte_invoice'

    nombre_reporte = 'domex.reporte_invoice3'

class ReportInvoice4(models.AbstractModel):
    _name = 'report.domex.reporte_invoice4'
    _inherit = 'domex.abstract.reporte_invoice'

    nombre_reporte = 'domex.reporte_invoice4'
