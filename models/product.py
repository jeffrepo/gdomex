# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from itertools import groupby
from operator import itemgetter
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tipo_gdomex = fields.Selection([('1', 'Accesorios'),('2', 'Molduras'),('4','Paneles'),('3', 'Otros')], string="Tipo")
    x_almex_id = fields.Integer(string="ALMEX ID", help="ID de Odoo 10 para sincronización")