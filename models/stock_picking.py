# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import time
from ast import literal_eval
from datetime import date, timedelta
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date
import logging
import datetime



class Picking(models.Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one('project.project')

    def _action_done(self):
        res = super()._action_done()
        self.env.context.get('active_ids')
        project = None
        logging.warning('Haciendo clic en alguna parte :::')
        logging.warning(self.env.context)
        # logging.warning(self.env.context['proyecto'])
        if 'proyecto' in self.env.context and self.env.context['proyecto']:
            project = self.env['project.project'].search([('id', '=', self.env.context['proyecto'])])
        else:
            transferencia = self.env['stock.picking'].search([('id', '=', self.env.context['active_id'])])
            project = transferencia.project_id

        if self.state == 'done':
            if project:
                if self.move_ids_without_package:
                    for linea in self.move_ids_without_package:
                        if linea.product_id.create_analytic_sale:
                            analytic_move_dic = {
                            'name': linea.product_id.name,
                            'account_id': project.sale_order_id.analytic_account_id.id,
                            'date': datetime.date.today(),
                            'amount': (linea.product_id.standard_price * -1)* linea.product_uom_qty,
                            'product_id': linea.product_id.id,
                            'picking_line_id': linea.id,
                            'unit_amount': linea.product_uom_qty }
                            analytic_move_id = self.env['account.analytic.line'].create(analytic_move_dic)

        doc_origin = ''
        if self.project_id and self.origin:
            logging.warning('Tenemos projecto /////////////')
            doc_origin = self.origin.split(" ")[-1]

            if doc_origin:
                lst_prod = []
                lst_stock_move = []
                transferencias = self.env['stock.picking'].search([('name', '=', doc_origin)])

                if transferencias:
                    for linea_retorno in self.move_ids_without_package:
                        for linea_transferencia in transferencias.move_ids_without_package:
                            if linea_retorno.product_id.id == linea_transferencia.product_id.id:
                                lst_stock_move.append(linea_transferencia.id)

            margen_bruto = self.env['account.analytic.line'].search([('picking_line_id', 'in', lst_stock_move)])

            for linea_cambio in self.move_ids_without_package:
                nueva_cantidad = 0
                nuevo_precio = 0
                for linea_cuenta_analitica in margen_bruto:
                    if linea_cambio.product_id.id == linea_cuenta_analitica.product_id.id:
                        if linea_cambio.product_uom_qty <= linea_cuenta_analitica.unit_amount:
                            nueva_cantidad = linea_cuenta_analitica.unit_amount - linea_cambio.product_uom_qty
                            nuevo_precio = nueva_cantidad * linea_cambio.product_id.standard_price

                            if nueva_cantidad > 0:
                                linea_cuenta_analitica.update({'unit_amount':nueva_cantidad, 'amount':nuevo_precio})
                            if nueva_cantidad == 0:
                                linea_cuenta_analitica.unlink()

        return True
