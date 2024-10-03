# -*- coding: utf-8 -*-

from odoo import models, fields, api

from functools import lru_cache
import logging

class ReportOrdenTrabajo(models.AbstractModel):
    _name = 'report.gdomex.report_orden_trabajo'
    _description = 'Creado para el envio de calculos al pdf'

    def calculo_otros(self, docs):
        transferencias_ids = docs.transferencias_ids

        cantidad = 0
        largo_gdomex = 0
        for trans in transferencias_ids:
            if trans.move_ids_without_package:
                for linea_operacion in trans.move_ids_without_package:
                    if linea_operacion.product_id.tipo_gdomex == '3':
                        cantidad += linea_operacion.product_uom_qty
                        largo_gdomex += linea_operacion.largo_gdomex

        total_metros_lineales = cantidad * largo_gdomex
        return total_metros_lineales

    def total_metros_lineales_paneles(self, docs):
        transferencias_ids = docs.transferencias_ids

        cantidad = 0
        largo_gdomex = 0
        total_metros_lineales = 0
        for trans in transferencias_ids:
            if trans.move_ids_without_package:
                for linea_operacion in trans.move_ids_without_package:
                    if linea_operacion.product_id.tipo_gdomex == '3' or linea_operacion.product_id.tipo_gdomex == '4':
                        #cantidad += linea_operacion.product_uom_qty
                        #largo_gdomex += linea_operacion.largo_gdomex
                       # total_metros_lineales += linea_operacion.product_uom_qty
                        total_metros_lineales += linea_operacion.quantity_done * linea_operacion.largo_gdomex
        #total_metros_lineales = cantidad * largo_gdomex
        return total_metros_lineales


    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['project.project'].browse(docids)
        docs = data.get('ids', data.get('active_ids'))
        logging.warning('update ')
        logging.warning(data)
        logging.warning(docs)
        trans_ids = data['form']['transferencias_ids']

        if 'form' in data and 'transferencias_ids' in data['form']:
            transferencias = self.env['stock.picking'].search([('id', 'in', trans_ids)])

        logging.warning('Transferencias ......')
        logging.warning(transferencias)

        logging.warning('')
        logging.warning('')
        # total_metros_lineales = self.calculo_otros(docs)
        # transferencias = data.get('form', {}).get('transferencias_ids', False)
        # proyecto = data.get('form', {}).get('proyecto', False)
        # logging.warning('reporte')
        # logging.warning(docids)
        # logging.warning(docs)
        # logging.warning(data)
        # logging.warning(proyecto)
        proyecto = self.env['project.project'].search([('id','=', docs[0])])
        logging.warning('el proyecto en report')
        logging.warning(proyecto)
        return {
            'doc_ids': docids,
            'doc_model': 'gdomex.report_orden_trabajo',
            'docs': docs,
            #'total_metros_lineales': total_metros_lineales,
            'total_metros_lineales_paneles': self.total_metros_lineales_paneles,
            'transferencias_ids': transferencias,
            'proyecto': [proyecto],
        }
