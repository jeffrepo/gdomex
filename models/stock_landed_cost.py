# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    compra_ids = fields.Many2many('purchase.order', string='Compras')
    costo_unitario_ids = fields.One2many('gdomex.costo_unitario_lineas','cost_id',string='Costo unitario')
    purchase_invoice_ids =  fields.Many2many('purchase.order', 'stock_landed_cost_purchase_rel',string="Factura compras")
    total_company_currency = fields.Float('Total compras moneda')
    total_cost = fields.Float('Total general')


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
            compra_con_gastos_productos = False
            for compra in coste.compra_ids:
                if compra.incluye_gastos == True:
                    compra_con_gastos_productos = True

            if compra_con_gastos_productos == False:
                for compra in coste.compra_ids:
                    for factura in compra.invoice_ids:
                        for linea_compra in factura.invoice_line_ids:
                            llave = linea_compra.product_id.id
                            if llave in productos:
                                unidad_gtq = linea_compra.currency_id._convert(linea_compra.price_unit,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                                precio_total = unidad_gtq * linea_compra.quantity
                                porcentaje = linea_compra.price_subtotal / compra.amount_total
                                gasto = total_gastos * porcentaje
                                costo = (gasto / linea_compra.quantity) + unidad_gtq
                                logging.warning(unidad_gtq)
                                logging.warning(precio_total)
                                logging.warning(porcentaje)
                                logging.warning(gasto)
                                logging.warning(costo)
                                productos[llave]['unidad_gtq'] = unidad_gtq
                                productos[llave]['precio_total'] = precio_total
                                productos[llave]['porcentaje'] = porcentaje
                                productos[llave]['costo'] = costo

                    # for linea_compra in compra.invoice_ids.invoice_line_ids:
                    #     llave = linea_compra.product_id.id
                    #     if llave in productos:
                    #         unidad_gtq = linea_compra.currency_id._convert(linea_compra.price_unit,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                    #         precio_total = unidad_gtq * linea_compra.quantity
                    #         porcentaje = linea_compra.price_subtotal / compra.amount_total
                    #         gasto = total_gastos * porcentaje
                    #         costo = (gasto / linea_compra.quantity) + unidad_gtq
                    #         logging.warning(unidad_gtq)
                    #         logging.warning(precio_total)
                    #         logging.warning(porcentaje)
                    #         logging.warning(gasto)
                    #         logging.warning(costo)
                    #         productos[llave]['unidad_gtq'] = unidad_gtq
                    #         productos[llave]['precio_total'] = precio_total
                    #         productos[llave]['porcentaje'] = porcentaje
                    #         productos[llave]['costo'] = costo
            else:
                logging.warning('no incliue')
                total_gastos_otras_compras = 0
                for compra in coste.compra_ids:
                    if compra.incluye_gastos == False:
                        if compra.invoice_ids:
                            for factura in compra.invoice_ids:
                                if factura.move_type == "in_refund":
                                    total_gastos_otras_compras += ((factura.amount_total * -1)/1.12)
                                else:
                                    total_gastos_otras_compras += (factura.amount_total/1.12)
                        else:
                            total_gastos_otras_compras += (compra.amount_total/1.12)


                total_gastos = 0
                cantidad_productos = 0
                costo_unitario = 0
                for compra in coste.compra_ids:
                    if compra.incluye_gastos:
                        for factura in compra.invoice_ids:

                            for linea_compra in factura.invoice_line_ids:
                                logging.warning(linea_compra.product_id.detailed_type)
                                if linea_compra.product_id.detailed_type == "service":
                                    if factura.move_type == "in_refund":
                                        total_gastos += (linea_compra.price_subtotal * -1)
                                    else:
                                        total_gastos += linea_compra.price_subtotal
                                else:
                                    cantidad_productos += linea_compra.product_qty

                logging.warning('cantidad productos')
                logging.warning(cantidad_productos)
                logging.warning(total_gastos_otras_compras)
                for compra in coste.compra_ids:
                    costo_unitario = total_gastos / cantidad_productos
                    for factura in compra.invoice_ids:
                        for linea_compra in factura.invoice_line_ids:
                            if linea_compra.product_id.detailed_type == "product":
                                llave = linea_compra.product_id.id
                                if llave in productos:

                                    unidad_usd = linea_compra.price_unit + costo_unitario
                                    unidad_gtq = linea_compra.currency_id._convert(unidad_usd,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                                    precio_total = unidad_gtq * linea_compra.product_qty
                                    costo = (total_gastos_otras_compras / linea_compra.product_qty) + unidad_gtq
                                    if factura.move_type == "in_refund":
                                        unidad_usd = (linea_compra.price_unit * -1) + costo_unitario
                                        unidad_gtq = linea_compra.currency_id._convert(unidad_usd,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                                        precio_total = unidad_gtq * linea_compra.product_qty
                                        costo = (total_gastos_otras_compras / linea_compra.product_qty) + unidad_gtq

                                    logging.warning('gasto_compra')
                                    logging.warning(total_gastos)
                                    logging.warning('unidad_usd')
                                    logging.warning(unidad_usd)

                                    logging.warning('unidad_gtq')
                                    logging.warning(unidad_gtq)
                                    productos[llave]['unidad_usd'] = unidad_usd
                                    productos[llave]['unidad_gtq'] = unidad_gtq
                                    productos[llave]['precio_total'] = precio_total
                                    productos[llave]['costo'] = costo

                    # for linea_compra in compra.order_line:
                    #     if linea_compra.product_id.detailed_type == "product":
                    #         llave = linea_compra.product_id.id
                    #         if llave in productos:
                    #             unidad_usd = linea_compra.price_unit + costo_unitario
                    #             unidad_gtq = linea_compra.currency_id._convert(unidad_usd,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
                    #             precio_total = unidad_gtq * linea_compra.product_qty
                    #             costo = (total_gastos_otras_compras / linea_compra.product_qty) + unidad_gtq
                    #             logging.warning('gasto_compra')
                    #             logging.warning(total_gastos)
                    #             logging.warning('unidad_usd')
                    #             logging.warning(unidad_usd)

                    #             logging.warning('unidad_gtq')
                    #             logging.warning(unidad_gtq)
                    #             productos[llave]['unidad_usd'] = unidad_usd
                    #             productos[llave]['unidad_gtq'] = unidad_gtq
                    #             productos[llave]['precio_total'] = precio_total
                    #             productos[llave]['costo'] = costo
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


    # def calcular_costo_unitario(self):
    #     for coste in self:
    #         if len(coste.costo_unitario_ids) > 0:
    #             coste.costo_unitario_ids.unlink()

    #         total_gastos = 0
    #         productos = {}
    #         for linea in coste.valuation_adjustment_lines:
    #             total_gastos += linea.additional_landed_cost
    #             if linea.product_id.id not in productos:
    #                 productos[linea.product_id.id] = {
    #                     'costo': 0.00,
    #                     'cantidad': linea.quantity,
    #                     'producto': linea.product_id.id,
    #                     'unidad_gtq': 0,
    #                     'precio_total': 0,
    #                     'porcentaje': 0,
    #                     'gasto': 0}
    #         compra_con_gastos_productos = False
    #         for compra in coste.compra_ids:
    #             if compra.incluye_gastos == True:
    #                 compra_con_gastos_productos = True

    #         if compra_con_gastos_productos == False:
    #             for compra in coste.compra_ids:
    #                 for linea_compra in compra.order_line:
    #                     llave = linea_compra.product_id.id
    #                     if llave in productos:
    #                         unidad_gtq = linea_compra.currency_id._convert(linea_compra.price_unit,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
    #                         precio_total = unidad_gtq * linea_compra.product_qty
    #                         porcentaje = linea_compra.price_subtotal / compra.amount_total
    #                         gasto = total_gastos * porcentaje
    #                         costo = (gasto / linea_compra.product_qty) + unidad_gtq
    #                         logging.warning(unidad_gtq)
    #                         logging.warning(precio_total)
    #                         logging.warning(porcentaje)
    #                         logging.warning(gasto)
    #                         logging.warning(costo)
    #                         productos[llave]['unidad_gtq'] = unidad_gtq
    #                         productos[llave]['precio_total'] = precio_total
    #                         productos[llave]['porcentaje'] = porcentaje
    #                         productos[llave]['costo'] = costo
    #         else:
    #             logging.warning('no incliue')
    #             total_gastos_otras_compras = 0
    #             for compra in coste.compra_ids:
    #                 if compra.incluye_gastos == False:
    #                     total_gastos_otras_compras += (compra.amount_total/1.12)


    #             total_gastos = 0
    #             cantidad_productos = 0
    #             costo_unitario = 0
    #             for compra in coste.compra_ids:
    #                 if compra.incluye_gastos:
    #                     for linea_compra in compra.order_line:
    #                         logging.warning(linea_compra.product_id.detailed_type)
    #                         if linea_compra.product_id.detailed_type == "service":
    #                             total_gastos += linea_compra.price_subtotal
    #                         else:
    #                             cantidad_productos += linea_compra.product_qty

    #             logging.warning('cantidad productos')
    #             logging.warning(cantidad_productos)
    #             logging.warning(total_gastos_otras_compras)
    #             for compra in coste.compra_ids:
    #                 costo_unitario = total_gastos / cantidad_productos
    #                 for linea_compra in compra.order_line:
    #                     if linea_compra.product_id.detailed_type == "product":
    #                         llave = linea_compra.product_id.id
    #                         if llave in productos:
    #                             unidad_usd = linea_compra.price_unit + costo_unitario
    #                             unidad_gtq = linea_compra.currency_id._convert(unidad_usd,linea_compra.company_id.currency_id,linea_compra.company_id,coste.date)
    #                             precio_total = unidad_gtq * linea_compra.product_qty
    #                             costo = (total_gastos_otras_compras / linea_compra.product_qty) + unidad_gtq
    #                             logging.warning('gasto_compra')
    #                             logging.warning(total_gastos)
    #                             logging.warning('unidad_usd')
    #                             logging.warning(unidad_usd)

    #                             logging.warning('unidad_gtq')
    #                             logging.warning(unidad_gtq)
    #                             productos[llave]['unidad_usd'] = unidad_usd
    #                             productos[llave]['unidad_gtq'] = unidad_gtq
    #                             productos[llave]['precio_total'] = precio_total
    #                             productos[llave]['costo'] = costo
    #         lineas = []
    #         if productos:
    #             for p in productos:
    #                 costo_unitario = productos[p]['costo']
    #                 dic ={
    #                     'producto_id': productos[p]['producto'],
    #                     'costo': costo_unitario,
    #                 }
    #                 coste.write({
    #                     'costo_unitario_ids': [(0,0, dic)]
    #                 })
    #     return True

    def cargar_compras(self):
        for importacion in self:
            if importacion.compra_ids:
                listas_compras = []
                total_moneda = 0.00
                total_general = 0.00
                for compra in importacion.compra_ids:
                    if compra.factura_importacion:
                        listas_compras.append(compra.id)
                        for factura in compra.invoice_ids:
                            total_moneda += factura.amount_total / compra.currency_rate
                            logging.warning('total_moneda')
                            logging.warning(total_moneda)
                    for factura in compra.invoice_ids:
                        if factura.invoice_line_ids:
                            for linea_compra in factura.invoice_line_ids:
                                existe_linea_compra_id = self.env['stock.landed.cost.lines'].search([('move_line_id','=',linea_compra.id)])
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
                                        'move_line_id': linea_compra.id,
                                        'cost_id': importacion.id,
                                    }
                                    if len(existe_linea_compra_id) == 0:
                                        linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)
                                    else:
                                        existe_linea_compra_id.unlink()
                                        linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)


                    # if compra.invoice_ids.invoice_line_ids:
                    #     for linea_compra in compra.invoice_ids.invoice_line_ids:
                    #         existe_linea_compra_id = self.env['stock.landed.cost.lines'].search([('move_line_id','=',linea_compra.id)])
                    #         if linea_compra.product_id.detailed_type == "service":
                    #             total_linea = linea_compra.price_subtotal
                    #             if linea_compra.currency_id.id != linea_compra.company_id.currency_id.id:
                    #                 total_linea = linea_compra.currency_id._convert(linea_compra.price_subtotal,linea_compra.company_id.currency_id,linea_compra.company_id,importacion.date)
                    #             dic_linea_costo = {
                    #                 'product_id': linea_compra.product_id.id,
                    #                 'name': linea_compra.name,
                    #                 'account_id': linea_compra.product_id.property_account_expense_id.id,
                    #                 'split_method': "by_current_cost_price",
                    #                 'price_unit': total_linea,
                    #                 'move_line_id': linea_compra.id,
                    #                 'cost_id': importacion.id,
                    #             }
                    #             if len(existe_linea_compra_id) == 0:
                    #                 linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)
                    #             else:
                    #                 existe_linea_compra_id.unlink()
                    #                 linea_costo_id = self.env['stock.landed.cost.lines'].create(dic_linea_costo)

                    importacion.purchase_invoice_ids = listas_compras
                    importacion.total_company_currency = total_moneda
                    importacion.total_cost = total_moneda + importacion.amount_total

class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    compra_linea_id = fields.Many2one('purchase.order.line','Linea de compra')
    move_line_id = fields.Many2one('account.move.line','Linea')
