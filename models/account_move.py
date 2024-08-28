# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"
    
    otro_comentario = fields.Char('Otro comentario')

    picking_id = fields.Many2one('stock.picking', string="Albarán")
    
    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            company_id = m.company_id.id or self.env.company.id
            if m.move_type != 'entry':
                journal_type = m.invoice_filter_type_domain or 'general'
                domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            else:
                journal_type = m.invoice_filter_type_domain or ['general','cash','bank']
                domain = [('company_id', '=', company_id), ('type', 'in', journal_type)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)



    def action_post(self):
        # Llamar al método original action_post
        res = super(AccountMove, self).action_post()
        
        for move in self:
            if move.company_id.id == 11 and move.move_type == 'out_invoice':
                has_storable_product = any(line.product_id.type == 'product' for line in move.invoice_line_ids)

                if has_storable_product:
                    # Crear el albarán
                    picking = self.env['stock.picking'].create({
                        'partner_id': move.partner_id.id,
                        'location_id': 148,  # Ubicación origen
                        'location_dest_id': 5,  # Clientes
                        'picking_type_id': 110,  # Tipo de picking
                        'origin': move.name,
                        'move_type': 'direct',  # Tipo de movimiento
                    })

                    for line in move.invoice_line_ids:
                        if line.product_id.type == 'product':  # Solo productos almacenables
                            self.env['stock.move'].create({
                                'name': line.name,
                                'product_id': line.product_id.id,
                                'product_uom_qty': line.quantity,
                                'product_uom': line.product_uom_id.id,
                                'picking_id': picking.id,
                                'location_id': 148,  # Ubicación origen
                                'location_dest_id': 5,  # Clientes
                            })

                    # Guardar la referencia del albarán en la factura
                    move.picking_id = picking.id
                    _logger.info(f'Albarán creado: {picking.name} para la factura {move.name}')
                else:
                    _logger.info(f'No se creó albarán para la factura {move.name} porque no contiene productos almacenables.')
            else:
                _logger.info(f'No se creó albarán para la factura {move.name}')
        
        return res
    


    def action_view_picking(self):
        self.ensure_one()
        if self.picking_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': self.picking_id.id,
                'target': 'current',
            }
        else:
            raise UserError('No hay un albarán asociado a esta factura.')

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_account(self):
        res = super()._get_computed_account()
        if self.move_id.journal_id.cuenta_default and self.move_id.is_sale_document(include_receipts=True):
            return self.move_id.journal_id.default_account_id
        else:
            return res