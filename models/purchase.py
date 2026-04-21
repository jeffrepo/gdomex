# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier = fields.Many2one('res.partner', string='Supplier')
    bill_to = fields.Many2one('res.partner', string='Bill to')
    consigned_to = fields.Many2one('res.partner', string='Consigned to')
    send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    marks = fields.Text(string="Marks")
    insurance = fields.Char('Insurance')
    delivery = fields.Char('Delivery')
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
    fecha_tipo_cambio = fields.Date("Fecha tipo cambio")
    x_almex_id = fields.Integer('Almex ID', help="ID de la orden de compra en Odoo 10")

    @api.model_create_multi
    def create(self, vals_list):
        sequence_by_picking_type = {
            127: 'purchase_order_gdomex_code',
            136: 'purchase_order_almex_code',
            155: 'purchase_order_domex_imp_code',
            154: 'purchase_order_almex_imp_code',
            73: 'purchase_order_bordalas_code',
            64: 'purchase_order_neira_code',
            55: 'purchase_order_acuario_code',
            354: 'purchase_order_inversionesk_code',
            363: 'purchase_order_corporacionk_code',
            399: 'purchase_order_aply_imp_code',
            390: 'purchase_order_sach_code',
            381: 'purchase_order_aply_code',
            165: 'purchase_order_armadillo_code',
            409: 'purchase_order_armadilloz_code',
            419: 'purchase_order_armadillo_imp_code',
            418: 'purchase_order_armadilloz_imp_code',
        }

        for vals in vals_list:
            company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
            self_comp = self.with_company(company_id)

            picking_type_id = vals.get('picking_type_id')
            sequence_code = sequence_by_picking_type.get(picking_type_id)

            if sequence_code and vals.get('name', 'New') == 'New':
                seq_date = None
                if vals.get('date_order'):
                    seq_date = fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(vals['date_order'])
                    )
                vals['name'] = self_comp.env['ir.sequence'].next_by_code(
                    sequence_code,
                    sequence_date=seq_date
                ) or '/'

        return super().create(vals_list)
