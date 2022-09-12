# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    no_negociable = fields.Boolean(string='No negociable',default=False)
    nombre_impreso = fields.Char(string='Nombre impreso')
