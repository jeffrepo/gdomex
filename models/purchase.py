# -*- coding: utf-8 -*-
from markupsafe import Markup
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier = fields.Many2one('res.partner', string='Supplier')
    bill_to = fields.Many2one('res.partner', string='Bill to')
    consigned_to = fields.Many2one('res.partner', string='Consigned to')
    send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    marks = fields.Text(string="Marks")
    insurance = fields.Char('Insurance')
    delivery = fields.Char('Delivery')

    # Ni idea de que sea esto ---------
    supplier_order_ref = fields.Char(string='Referencia proveedor')
    bill_to = fields.Many2one('res.partner', string='Bill to')
    consigned_to = fields.Many2one('res.partner', string='Consigned to')
    send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    marks = fields.Text(string="Marks")
    insurance = fields.Char('Insurance')
    delivery = fields.Char('Delivery')
    proyecto = fields.Char('Proyecto')
    solicitante = fields.Many2one('res.partner', string='Solicitante')
    lugar_entrega = fields.Char('Lugar de entrega')
