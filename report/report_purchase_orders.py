# -*- coding: utf-8 -*-

from odoo import api, models
import re
import datetime
from datetime import date
import logging

class ReportPurchaseOrders(models.AbstractModel):
    _name = 'report.gdomex.purchase_orders'

    def fecha_impresion(self):
        fecha = str(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date())
        return fecha
    
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(docids)
        company_id = False
        logging.warning('reporte fecha')
        logging.warning(self.fecha_impresion)
        if data:
            company_id = self.env.company

        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'fecha_impresion': self.fecha_impresion,
            'company': company_id,
            'docs': docs,
        }
