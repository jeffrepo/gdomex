# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

class gdomex_project_orden_trabajo(models.TransientModel):
    _name = 'gdomex.report_orden_trabajo'

    def _default_transferencias(self):
        if len(self.env.context.get('active_ids', [])) > 0:
            pj = self.env.context.get('active_ids')[0]
            project = self.env['project.project'].search([('id','=', pj)])
            pickings = False
            if project:
                pickings =  [x.id for x in project.transferencias_ids]

            return [(6,0, pickings)]
        else:
            return None

    anio = fields.Integer('Año')
    transferencias_ids = fields.Many2many('stock.picking', string='Transferencias',default=_default_transferencias)

    def print_report(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['transferencias_ids'])
        res = res and res[0] or {}
        logging.warning('el res')
        logging.warning(res)
        res['proyecto'] =  datas['ids'][0]
        datas['form'] = res
        logging.warning('actual')
        logging.warning(datas)
        return self.env.ref('gdomex.action_project_orden_trabajo').report_action([], data=datas)
