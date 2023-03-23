# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class Color(models.Model):
    _name = 'domex.color'

    name = fields.Char("Nombre")

class DomexPresupuestoProductoLinea(models.Model):
    _name = 'domex.presupuesto_producto_linea'

    project_id = fields.Many2one('project.project', string='Proyecto')
    producto_id = fields.Many2one('product.product', string='Producto')
    cantidad = fields.Float('Cantidad')

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    largo = fields.Float('Largo')
    ancho = fields.Float('Ancho')
    color_id = fields.Many2one('domex.color', string='Color')
    calibre = fields.Float('Calibre')
    aislante = fields.Char('Aislante')
    cantidad_planchas = fields.Integer('Cantidad de planchas')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    largo = fields.Float('Largo')
    ancho = fields.Float('Ancho')
    color_id = fields.Many2one('domex.color', string='Color')
    calibre = fields.Float('Calibre')
    aislante = fields.Char('Aislante')
    cantidad_planchas = fields.Integer('Cantidad de planchas')

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    multiplicador_materia = fields.Float('Multiplicador materia')

    # @api.multi
    def multiplicar(self):
        for production in self:
            for m in production.move_raw_ids:
                m.quantity_done = m.product_uom_qty * production.multiplicador_materia - m.product_uom_qty
                # m.product_qty = m.product_qty * production.multiplicador_materia
                # m.product_uom_qty = m.product_uom_qty * production.multiplicador_materia
                # m.ordered_qty = m.ordered_qty * production.multiplicador_materia
        return True

# class SaleOrder(models.Model):
#     _inherit = "sale.order"
#
#     proyecto = fields.Char('Proyecto')
#     atencion = fields.Many2one('res.partner', string='Atención')
#     supplier = fields.Many2one('res.partner', string='Supplier')
#     bill_to = fields.Many2one('res.partner', string='Bill to')
#     consigned_to = fields.Many2one('res.partner', string='Consigned to')
#     send_docs_to = fields.Many2one('res.partner', string='Send Docs to')
#     marks = fields.Text(string="Marks")
#     insurance = fields.Char('Insurance')
#     delivery = fields.Char('Delivery')
#     comision = fields.Float('Comision de ventas')
#     lugar_entrega = fields.Char('Lugar de entrega')
#     tiempo_estimado_entrega = fields.Char('Tiempo estimado de entrega')
#     medidas = fields.Char('De acuerdo a')
#     oferta_por = fields.Char("Oferta por")
#     no_incluyen = fields.Text("Precios no incluyen")
#     incluyen = fields.Char("Precios incluyen")
#     tiempo_instalacion = fields.Char("Tiempo de instalación")

    # # @api.multi
    # def recalcular_totales(self):
    #     for order in self:
    #         for line in order.order_line:
    #             line.price_unit = line.price_unit * line.largo
    #     return True

# class StockPicking(models.Model):
#     _inherit = "stock.picking"
#
#     encargado_entrega = fields.Many2one('res.users', string='Encargado de la entrega')
#
#     def obtener_medidas(self, quant_ids):
#         res = []
#         medidas_agrupadas = {}
#         for quant in quant_ids:
#             if quant.lot_id.largo not in medidas_agrupadas:
#                 medidas_agrupadas[quant.lot_id.largo] = {'medida': quant.lot_id.largo, 'cantidad': 0}
#             medidas_agrupadas[quant.lot_id.largo]['cantidad'] += quant.qty
#         res = medidas_agrupadas.values()
#         return res


# class OrdenTrabajo(models.Model):
#     _inherit = 'orden.trabajo'
#
#     fecha_produccion = fields.Date('Fecha de Producción')
#     observaciones = fields.Text(string="Observaciones")
#     revisado_por = fields.Many2one('res.users', string='Revisado por')
#     autorizado_por = fields.Many2one('res.users', string='Autorizado por')
#
#     def obtener_cortes(self, cortes):
#         res = []
#         cortes_agrupados = {}
#         for line in cortes:
#             if line.corte1 not in cortes_agrupados:
#                 cortes_agrupados[line.corte1] = {'medida': line.corte1, 'cantidad': 0}
#             cortes_agrupados[line.corte1]['cantidad'] += line.product_qty
#             if line.corte2 not in cortes_agrupados:
#                 cortes_agrupados[line.corte2] = {'medida': line.corte2, 'cantidad': 0}
#             cortes_agrupados[line.corte2]['cantidad'] += line.product_qty
#             if line.corte3 not in cortes_agrupados:
#                 cortes_agrupados[line.corte3] = {'medida': line.corte3, 'cantidad': 0}
#             cortes_agrupados[line.corte3]['cantidad'] += line.product_qty
#             if line.corte4 not in cortes_agrupados:
#                 cortes_agrupados[line.corte4] = {'medida': line.corte4, 'cantidad': 0}
#             cortes_agrupados[line.corte4]['cantidad'] += line.product_qty
#             if line.corte5 not in cortes_agrupados:
#                 cortes_agrupados[line.corte5] = {'medida': line.corte5, 'cantidad': 0}
#             cortes_agrupados[line.corte5]['cantidad'] += line.product_qty
#             if line.corte6 not in cortes_agrupados:
#                 cortes_agrupados[line.corte6] = {'medida': line.corte6, 'cantidad': 0}
#             cortes_agrupados[line.corte6]['cantidad'] += line.product_qty
#             if line.sobra not in cortes_agrupados:
#                 cortes_agrupados[line.sobra] = {'medida': line.sobra, 'cantidad': 0}
#             cortes_agrupados[line.sobra]['cantidad'] += line.product_qty
#
#         res = cortes_agrupados.values()
#         return res


class AccountMove(models.Model):
    _inherit = "account.move"

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Tipo de Gasto")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tipo_gasto = fields.Selection([('compra', 'Compra/Bien'), ('servicio', 'Servicio'), ('importacion', 'Importación/Exportación'), ('combustible', 'Combustible'), ('mixto', 'Mixto')], string="Tipo de Gasto", related='move_id.tipo_gasto',store=True)
