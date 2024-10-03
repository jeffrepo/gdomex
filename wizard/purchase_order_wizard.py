# -*- encoding: utf-8 -*-
from odoo import api, fields, models
import logging


class WizardPurchaseOrder(models.TransientModel):
    _name = "gdomex.wizard_po"

    company_id = fields.Many2one('res.company', string='Compañía', required=True)

    # @api.multi
    # def print_report(self):
    #     """Metodo que llama la lógica que genera el reporte"""
    #     logging.warning('Activando función print_report')
    #     logging.warning('')
    #     datas={'ids': self.env.context.get('active_ids', [])}
    #     res = self.read(['company_id'])
    #     res = res and res[0] or {}
    #     datas['form'] = res
    #     return self.env['report'].get_action([], 'gdomex.purchase_orders_report', data=datas)


    def print_report(self):
        data = {
             'ids': [],
             'model': 'gdomex.wizard_po',
             'form': self.read()[0]
        }
        return self.env.ref('gdomex.report_purchase_orders').report_action([], data=data)
