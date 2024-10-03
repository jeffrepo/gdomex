# -*- coding: utf-8 -*-

from odoo import api, models
import re
import datetime
from datetime import date
import logging

class ReportPurchaseOrder(models.AbstractModel):
    _name = 'report.gdomex.purchase_orders_report'

    def fecha_impresion(self):
        fecha = str(datetime.datetime.strptime(str(date.today()), '%Y-%m-%d').date())
        return fecha

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['purchase.order'].browse(docids)
        company_id = False

        if data:
            company_id = self.env.company

        return {
            'doc_ids': docids,
            'doc_model': 'purchase.order',
            'fecha_impresion': self.fecha_impresion,
            'company': company_id,
            'docs': docs,
        }


    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     model = self.env.context.get('active_model')
    #     data = data if data is not None else {}
    #     company_id = False
    #     # self.model = 'purchase.order'
    #     # docs = self.env[model].browse(data.get('ids', data.get('active_ids')))
    #     docs = self.env['purchase.order'].browse(self.env.context.get('active_ids', []))
    #     logging.warning('data?')
    #     logging.warning(data)
    #     logging.warning(self.env.company.id)
    #     if data:
    #         company_id = self.env.company
    #     logging.warning(company_id.name)
    #     logging.warning(docs)
    #     return {
    #         'doc_ids': data.get('ids', data.get('active_ids')),
    #         'doc_model': model,
    #         'docs': docs,
    #         'fecha_impresion': self.fecha_impresion,
    #         'company': company_id,
    #         'data': dict(
    #             data
    #         ),
    #     }
        # return self.env['report'].render('gdomex.purchase_orders_report', docargs)


    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     logging.warning('función _get_report_values')
    #     model = self.env.context.get('active_model')
    #     docs = self.env[model].browse(self.env.context.get('active_ids', []))
    #     logging.warn(data)
    #     return {
    #         'doc_ids': self.ids,
    #         'doc_model': model,
    #         'data': data['form'],
    #         'docs': docs,
    #     }
