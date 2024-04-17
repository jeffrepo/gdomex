# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    por_facturar = fields.Monetary('Por facturar', compute='_new_total_invoice', store=True)
    proyecto = fields.Char('Proyecto')
    atencion = fields.Many2one('res.partner', string='Atención')
    supplier = fields.Many2one('res.partner', string='Supplier')
    bill_to = fields.Many2one('res.partner', string='Bill to')
    consigned_to = fields.Many2one('res.partner', string='Consigned to')
    send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
    marks = fields.Text(string="Marks")
    insurance = fields.Char('Insurance')
    delivery = fields.Char('Delivery')
    comision = fields.Float('Comision de ventas')
    lugar_entrega = fields.Char('Lugar de entrega')
    tiempo_estimado_entrega = fields.Char('Tiempo estimado de entrega')
    medidas = fields.Char('De acuerdo a')
    oferta_por = fields.Char("Oferta por")
    no_incluyen = fields.Text("Precios no incluyen")
    incluyen = fields.Char("Precios incluyen")
    tiempo_instalacion = fields.Char("Tiempo de instalación")
    forma_pago = fields.Char("Forma de pago")

    @api.depends('order_line.price_total', 'invoice_ids', 'invoice_count')
    def _new_total_invoice(self):
        for order in self:
            order.por_facturar = order.amount_total
            if order.invoice_ids:
                total_facturas = 0
                for factura in order.invoice_ids:
                    if factura.state == 'posted':
                        if factura.amount_total_signed > 0 and order.amount_total > 0:

                            total_facturas += factura.amount_total_signed
                            order.por_facturar = order.amount_total - total_facturas

                if order.por_facturar == 0:
                    order.invoice_status = 'invoiced'

    # # @api.multi
    def recalcular_totales(self):
        for order in self:
            for line in order.order_line:
                line.price_unit = line.price_unit * line.largo
        return True

    @api.model
    def create(self, vals):
        if 'date_order' in vals:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            if vals['warehouse_id'] == 1:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale_order_gdomex_code', sequence_date=seq_date) or _('New')
            if vals['warehouse_id'] == 10:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale_order_almex_code', sequence_date=seq_date) or _('New')
            if vals['warehouse_id'] == 9:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale_order_bordalas_code', sequence_date=seq_date) or _('New')
            if vals['warehouse_id'] == 8:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale_order_neira_code', sequence_date=seq_date) or _('New')
            if vals['warehouse_id'] == 7:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale_order_acuario_code', sequence_date=seq_date) or _('New')

        result = super(SaleOrder, self).create(vals)
        if 'warehouse_id' in vals:
            warehouse_id = self.env['stock.warehouse'].search([('id','=', vals['warehouse_id'])])
            if warehouse_id:
                result.message_post(body=_("Almacen %s ", warehouse_id.name))
        return result

    def write(self, values):
        if self.warehouse_id and 'warehouse_id' in values:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(self.date_order))
            if values['warehouse_id'] == 1:
                values['name'] = self.env['ir.sequence'].next_by_code('sale_order_gdomex_code', sequence_date=seq_date) or _('New')
            if values['warehouse_id'] == 10:
                values['name'] = self.env['ir.sequence'].next_by_code('sale_order_almex_code', sequence_date=seq_date) or _('New')
            if values['warehouse_id'] == 9:
                values['name'] = self.env['ir.sequence'].next_by_code('sale_order_bordalas_code', sequence_date=seq_date) or _('New')
            if values['warehouse_id'] == 8:
                values['name'] = self.env['ir.sequence'].next_by_code('sale_order_neira_code', sequence_date=seq_date) or _('New')
            if values['warehouse_id'] == 7:
                values['name'] = self.env['ir.sequence'].next_by_code('sale_order_acuario_code', sequence_date=seq_date) or _('New')
        result = super(SaleOrder, self).write(values)
        return result

    def create_mrp_order(self):
        productos_dic = {}
        for sale in self:
            if sale.state in ['done','sale']:
                if sale.order_line:
                    for line in sale.order_line:
                        logging.warning('1')
                        logging.warning(line.product_id.bom_ids)
                        logging.warning(line.mrp_id)
                        if len(line.product_id.bom_ids) > 0 and len(line.mrp_id) == 0:
                            if line.product_id.id not in productos_dic:
                                logging.warning(line)
                                mrp_order_d = {
                                    'product_id': line.product_id.id,
                                    'product_uom_id': line.product_uom.id,
                                    'product_qty': line.product_uom_qty,
                                    'bom_id': line.product_id.bom_ids.id,
                                    'origin': line.order_id.name,
                                    'unidad': line.unidad,
                                    'largo': line.largo,
                                    'lines': [],
                                }
                                productos_dic[line.product_id.id] = mrp_order_d
                            productos_dic[line.product_id.id]['product_qty'] += line.product_uom_qty
                            productos_dic[line.product_id.id]['lines'].append(line)
        logging.warning('productos')
        logging.warning(productos_dic)
        if productos_dic:
            for p in productos_dic:
                mrp_order = {
                    'product_id':  productos_dic[p]['product_id'],
                    'product_uom_id': productos_dic[p]['product_uom_id'],
                    'product_qty': productos_dic[p]['product_qty'],
                    'origin': productos_dic[p]['origin'],
                    'unidad': productos_dic[p]['unidad'],
                    'bom_id': productos_dic[p]['bom_id'],
                    'largo': productos_dic[p]['largo'],


                }
                mrp_order_id = self.env['mrp.production'].create(mrp_order)
                #mrp_order_id._onchange_product_id()
                #mrp_order_id._onchange_bom_id()
                mrp_order_id._onchange_move_raw()
                # mrp_order_id._onchange_move_finished()
                for l in productos_dic[p]['lines']:
                    l.mrp_id = mrp_order_id.id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    unidad = fields.Float('Unidad')
    ancho = fields.Float('Ancho')
    largo = fields.Float('Largo')
    mrp_id = fields.Many2one('mrp.production','Fabricación')

    @api.onchange('unidad','largo','product_id')
    def _onchange_domex_largo(self):
        if self.unidad > 0 or self.largo > 0:
            self.product_uom_qty = self.unidad * self.largo
