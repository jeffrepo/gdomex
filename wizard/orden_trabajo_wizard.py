# -*- coding: utf-8 -*-

from odoo import models, fields, api
import xlsxwriter
import base64
import io
import logging

class OrdenTrabajoWizard(models.TransientModel):
    _name ="gdomex.orden_trabajo.wizard"
    _description ="Wizard creado para orden trabajo"

    name = fields.Char('Nombre archivo: ', size=32)
    archivo = fields.Binary('Archivo ', filters='.xls')

    def print_report(self):
        logging.warning('self.read()[0]')
        logging.warning(self.read()[0])
        data = {
            'ids':[],
            'model': 'gdomex.orden_trabajo_wizard.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('gdomex.action_orden_trabajo').report_action([], data=data)

    def print_report_excel(self):
        logging.warning('Estamos funcionando bien :D')

        
