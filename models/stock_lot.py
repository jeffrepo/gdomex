# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import logging

class ProductionLot(models.Model):
    _inherit = 'stock.lot'

    largo = fields.Float('Largo')
    ancho = fields.Float('Ancho')
    color_id = fields.Many2one('domex.color', string='Color')
    calibre = fields.Float('Calibre')
    aislante = fields.Char('Aislante')
    cantidad_planchas = fields.Integer('Cantidad de planchas')


    metros_reales = fields.Float('Metros reales')
    factor = fields.Float('Factor')
    proveedor_id = fields.Many2one('res.partner','Proveedor', store=True,  compute='_obtener_compra')
    orden_compra_id = fields.Many2one('purchase.order','Orden de compra', store=True, compute='_obtener_compra')

    @api.depends('product_id','purchase_order_ids')
    def _obtener_compra(self):
        for line in self:
            if len(line.purchase_order_ids) > 0:
                line.orden_compra_id = line.purchase_order_ids.id
                line.proveedor_id = line.purchase_order_ids.partner_id.id


    @api.depends('name')
    def _compute_purchase_order_ids(self):
        res = super(ProductionLot, self)._compute_purchase_order_ids()
        for lot in self:
            if len(lot.purchase_order_ids) > 0:
                lot.proveedor_id = lot.purchase_order_ids[0].partner_id.id
                lot.orden_compra_id = lot.purchase_order_ids[0].id
        return res
