# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

class AccountJournal(models.Model):
    _inherit = "account.journal"

    cuenta_default = fields.Boolean('Utilizar cuenta por default')