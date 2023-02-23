from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools.sql import column_exists, create_column

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one('project.project')
    encargado_entrega = fields.Many2one('res.users', string='Encargado de la entrega')
    recibe = fields.Char(string='Recibe')
    dpi = fields.Char(string='DPI')
    placas = fields.Char(string='Placas')
    entrega = fields.Char(string='Entrega')

    def obtener_medidas(self, quant_ids):
        res = []
        medidas_agrupadas = {}
        for quant in quant_ids:
            if quant.lot_id.largo not in medidas_agrupadas:
                medidas_agrupadas[quant.lot_id.largo] = {'medida': quant.lot_id.largo, 'cantidad': 0}
            medidas_agrupadas[quant.lot_id.largo]['cantidad'] += quant.qty
        res = medidas_agrupadas.values()
        return res

    def _action_done(self):
        res = super()._action_done()
        self.env.context.get('active_ids')
        project = None
        logging.warning('Haciendo clic en alguna parte :::')
        logging.warning(self.env.context)
        # logging.warning(self.env.context['proyecto'])
        if 'proyecto' in self.env.context and self.env.context['proyecto']:
            project = self.env['project.project'].search([('id', '=', self.env.context['proyecto'])])
        else:
            transferencia = self.env['stock.picking'].search([('id', '=', self.env.context['active_id'])])
            project = transferencia.project_id

        if self.state == 'done':
            if project:
                if self.move_ids_without_package:
                    for linea in self.move_ids_without_package:
                        if linea.product_id.create_analytic_sale:
                            analytic_move_dic = {
                            'name': linea.product_id.name,
                            'account_id': project.sale_order_id.analytic_account_id.id,
                            'date': datetime.date.today(),
                            'amount': (linea.product_id.standard_price * -1)* linea.product_uom_qty,
                            'product_id': linea.product_id.id,
                            'picking_line_id': linea.id,
                            'unit_amount': linea.product_uom_qty }
                            analytic_move_id = self.env['account.analytic.line'].create(analytic_move_dic)

        doc_origin = ''
        if self.project_id and self.origin:
            logging.warning('Tenemos projecto /////////////')
            doc_origin = self.origin.split(" ")[-1]

            if doc_origin:
                lst_prod = []
                lst_stock_move = []
                transferencias = self.env['stock.picking'].search([('name', '=', doc_origin)])

                if transferencias:
                    for linea_retorno in self.move_ids_without_package:
                        for linea_transferencia in transferencias.move_ids_without_package:
                            if linea_retorno.product_id.id == linea_transferencia.product_id.id:
                                lst_stock_move.append(linea_transferencia.id)

            margen_bruto = self.env['account.analytic.line'].search([('picking_line_id', 'in', lst_stock_move)])

            for linea_cambio in self.move_ids_without_package:
                nueva_cantidad = 0
                nuevo_precio = 0
                for linea_cuenta_analitica in margen_bruto:
                    if linea_cambio.product_id.id == linea_cuenta_analitica.product_id.id:
                        if linea_cambio.product_uom_qty <= linea_cuenta_analitica.unit_amount:
                            nueva_cantidad = linea_cuenta_analitica.unit_amount - linea_cambio.product_uom_qty
                            nuevo_precio = nueva_cantidad * linea_cambio.product_id.standard_price

                            if nueva_cantidad > 0:
                                linea_cuenta_analitica.update({'unit_amount':nueva_cantidad, 'amount':nuevo_precio})
                            if nueva_cantidad == 0:
                                linea_cuenta_analitica.unlink()

        return True
