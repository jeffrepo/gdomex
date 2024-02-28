# -*- coding: utf-8 -*-

from odoo import api, models
import re
import datetime
from datetime import date
import logging

class ReportContraseniasPago(models.AbstractModel):
    _name = 'report.gdomex.contrasenia_pago'

    def fecha_impresion(self):
        fecha = str(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date())
        return fecha

    def _get_facturas(self,facturas):
        factura_dic = {}
        nombre_empresa = False
        for factura in facturas:
            if factura.partner_id.id not in factura_dic:
                serie = ''
                numero = ''
                if factura.ref:
                    split = factura.ref.split('-')
                    if len(split) > 0:
                        serie = split[0]
                    if len(split) > 1:
                        numero = split[1]
                factura_dic.update({factura.partner_id.id: {'compras': [],'facturas':[],'nombre': factura.partner_id.name, 'nit': factura.partner_id.vat, 'serie': serie, 'currency': factura.currency_id, 'numero': numero, 'total':0}   })
            factura_dic[factura.partner_id.id]['total'] += factura.amount_total
            factura_dic[factura.partner_id.id]['compras'].append(factura.invoice_line_ids[0].purchase_order_id.name)
            factura_dic[factura.partner_id.id]['facturas'].append(factura)
            nombre_empresa = factura.invoice_line_ids[0].purchase_order_id.picking_type_id.warehouse_id.name
        primer_proveedor = next(iter(factura_dic))
        factura_dic = factura_dic[primer_proveedor]
        factura_dic['compras'] = (','.join(factura_dic['compras'])) if factura_dic['compras'][0] != False else ''
        return [factura_dic, nombre_empresa]

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        company_id = False
        if data:
            company_id = self.env.company
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'fecha_impresion': self.fecha_impresion,
            'company': company_id,
            'docs': docs,
            '_get_facturas': self._get_facturas,
        }
