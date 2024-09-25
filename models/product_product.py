
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from itertools import groupby
from operator import itemgetter
from datetime import date


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _track = False

    x_almex_id = fields.Integer(string="ALMEX ID", help="ID del producto en Odoo 10")