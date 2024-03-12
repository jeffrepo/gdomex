# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    nombre_impreso = fields.Char(string='Nombre impreso')

    def _create_payment_vals_from_wizard(self):
        vals = super()._create_payment_vals_from_wizard()
        if self.nombre_impreso:
            vals.update({'nombre_impreso': self.nombre_impreso})
        return vals