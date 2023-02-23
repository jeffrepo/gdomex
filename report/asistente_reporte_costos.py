# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
# from openerp.exceptions import UserError, ValidationError
import xlwt
import base64
try:
    import StringIO
except ImportError:
    from io import StringIO

import logging

class AsistenteReporteCostoInventarioMetros(models.TransientModel):
    _name = 'domex.asistente_reporte_costo_metros'

    producto_ids = fields.Many2many("product.product", string="Productos", required=True)
    name = fields.Char('Nombre archivo', size=32)
    archivo = fields.Binary('Archivo', filters='.xls')


    def reporte_excel(self):
        for w in self:
            libro = xlwt.Workbook()
            hoja = libro.add_sheet('reporte')

            xlwt.add_palette_colour("custom_colour", 0x21)
            libro.set_colour_RGB(0x21, 200, 200, 200)
            estilo = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
            hoja.write(0, 0, 'COSTO DE INVENTARIO EN METROS')

            y = 2

            for producto in w.producto_ids:
                hoja.write(y, 0, producto.name)
                y += 1
                hoja.write(y, 0, 'Lote')
                hoja.write(y, 1, 'Cantidad')
                hoja.write(y, 2, 'Cantidad en metros')
                hoja.write(y, 3, 'Costo por metro')
                hoja.write(y, 4, 'Costo total en metros')
                y += 1
                quants = self.env['stock.quant'].search([('product_id', '=', producto.id)])
                lineas = {}
                for q in quants:
                    if q.lot_id:
                        lote = q.lot_id.name
                    else:
                        lote = 'Indefinido'

                    if lote not in lineas:
                        lineas[lote] = {'cantidad': 0, 'cantidad_en_metros': 0, 'costo_por_metro': q.product_id.costo_por_metro, 'costo_total_en_metros': 0}
                    lineas[lote]['cantidad'] += q.qty
                    lineas[lote]['cantidad_en_metros'] += q.cantidad_en_metros
                    lineas[lote]['costo_total_en_metros'] += q.costo_total_en_metros

                for lote in lineas:
                    hoja.write(y, 0, lote)
                    hoja.write(y, 1, lineas[lote]['cantidad'])
                    hoja.write(y, 2, lineas[lote]['cantidad_en_metros'])
                    hoja.write(y, 3, lineas[lote]['costo_por_metro'])
                    hoja.write(y, 4, lineas[lote]['costo_total_en_metros'])
                    y += 1

                y += 3

            f = StringIO.StringIO()
            libro.save(f)
            datos = base64.b64encode(f.getvalue())
            self.write({'archivo':datos, 'name':'costo_inventario_metros.xls'})

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'domex.asistente_reporte_costo_metros',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
