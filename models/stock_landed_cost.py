# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _



class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    compra_ids = fields.Many2many('purchase.order', string='Compras')

    def cargar_compras(self):
        for importacion in self:
            if importacion.compra_ids:
                for compra in importacion.compra_ids:
                    if compra.order_line:
                        for linea_compra in compra.order_line:
                            existe_linea_compra_id = self.env['stock.landed.cost.lines'].search([('compra_linea_id','=',linea_compra.id)])
                            if linea_compra.product_id.detailed_type == "service":
                                dic_linea_costo = {
                                    'product_id': linea_compra.product_id.id,
                                    'name': linea_compra.name,
                                    'account_id': linea_compra.product_id.property_account_expense_id.id,
                                    'split_method': "by_current_cost_price",
                                    'price_unit': linea_compra.price_subtotal,
                                    'compra_linea_id': linea_compra.id,
                                    'cost_id': importacion.id,
                                }
                                if len(existe_linea_compra_id) == 0:
                                    linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)
                                else:
                                    existe_linea_compra_id.unlink()
                                    linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)

class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    compra_linea_id = fields.Many2one('purchase.order.line','Linea de compra')
