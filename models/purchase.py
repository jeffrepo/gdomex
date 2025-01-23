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
    #bill_to = fields.Many2one('res.partner', string='Bill to')
    #consigned_to = fields.Many2one('res.partner', string='Consigned to')
    #send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    #marks = fields.Text(string="Marks")
    #insurance = fields.Char('Insurance')
    #delivery = fields.Char('Delivery')
    proyecto = fields.Char('Proyecto')
    solicitante = fields.Many2one('res.partner', string='Solicitante')
    lugar_entrega = fields.Char('Lugar de entrega')
    incluye_gastos = fields.Boolean('Incluye gastos', tracking=True)
    factura_importacion = fields.Boolean('Factura importacion', tracking=True)

    x_almex_id = fields.Integer('Almex ID', help="ID de la orden de compra en Odoo 10")

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)
        if 'picking_type_id' in vals:
            if vals['picking_type_id'] == 127:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_gdomex_code', sequence_date=seq_date) or '/'
            if vals['picking_type_id'] == 136:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_almex_code', sequence_date=seq_date) or '/'
                    
            if vals['picking_type_id'] == 155:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_domex_imp_code', sequence_date=seq_date) or '/'
                    
            if vals['picking_type_id'] == 154:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_almex_imp_code', sequence_date=seq_date) or '/'
            if vals['picking_type_id'] == 73:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_bordalas_code', sequence_date=seq_date) or '/'
            if vals['picking_type_id'] == 64:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_neira_code', sequence_date=seq_date) or '/'
            if vals['picking_type_id'] == 55:

                if vals.get('name', 'New') == 'New':
                    seq_date = None
                    if 'date_order' in vals:
                        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
                    vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase_order_acuario_code', sequence_date=seq_date) or '/'
        result = super(PurchaseOrder, self).create(vals)
        return result
