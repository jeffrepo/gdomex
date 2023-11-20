# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _



class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    compra_ids = fields.Many2many('purchase.order', string='Compras')
    costo_unitario_ids = fields.One2many('gdomex.costo_unitario_lineas','cost_id',string='Costo unitario')
    
    def calcular_costo_unitario(self):
        for coste in self:
            if len(coste.costo_unitario_ids) > 0:
                coste.costo_unitario_ids.unlink()

            total_gastos = 0
            productos = {}
            for linea in coste.valuation_adjustment_lines:
                total_gastos += linea.additional_landed_cost
                if linea.product_id.id not in productos:
                    productos[linea.product_id.id] = {
                        'costo': 0.00, 
                        'cantidad': linea.quantity, 
                        'producto': linea.product_id.id,
                        'unidad_gtq': 0,
                        'precio_total': 0,
                        'porcentaje': 0,
                        'gasto': 0}
                    
            for compra in coste.compra_ids:
                for linea_compra in compra.order_line:
                    llave = linea_compra.product_id.id
                    if llave in productos:
                        unidad_gtq = linea_compra.currency_id._convert(linea_compra.price_unit,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                        precio_total = unidad_gtq * linea_compra.product_qty
                        porcentaje = linea_compra.price_subtotal / compra.amount_total
                        gasto = total_gastos * porcentaje
                        costo = (gasto / linea_compra.product_qty) + unidad_gtq
                        productos[llave]['unidad_gtq'] = unidad_gtq
                        productos[llave]['precio_total'] = precio_total
                        productos[llave]['porcentaje'] = porcentaje
                        productos[llave]['costo'] = costo
                    
            lineas = []
            if productos:
                for p in productos:
                    costo_unitario = productos[p]['costo']
                    dic ={
                        'producto_id': productos[p]['producto'],
                        'costo': costo_unitario,
                    }
                    coste.write({
                        'costo_unitario_ids': [(0,0, dic)]
                    })
        return True
        
    def cargar_compras(self):
        for importacion in self:
            if importacion.compra_ids:
                for compra in importacion.compra_ids:
                    if compra.order_line:
                        for linea_compra in compra.order_line:
                            existe_linea_compra_id = self.env['stock.landed.cost.lines'].search([('compra_linea_id','=',linea_compra.id)])
                            if linea_compra.product_id.detailed_type == "service":
                                total_linea = linea_compra.price_subtotal
                                if linea_compra.currency_id.id != linea_compra.company_id.currency_id.id:
                                    total_linea = linea_compra.currency_id._convert(linea_compra.price_subtotal,linea_compra.company_id.currency_id,linea_compra.company_id,importacion.date)
                                dic_linea_costo = {
                                    'product_id': linea_compra.product_id.id,
                                    'name': linea_compra.name,
                                    'account_id': linea_compra.product_id.property_account_expense_id.id,
                                    'split_method': "by_current_cost_price",
                                    'price_unit': total_linea,
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
