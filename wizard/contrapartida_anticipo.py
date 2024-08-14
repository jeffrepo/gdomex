# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

class gdomex_contrapartida_wizard(models.TransientModel):
    _name = 'gdomex.contrapartida.wizard'

    cuenta_destino_id = fields.Many2one('account.account', 'Cuenta destino', required=True)
    diario_id = fields.Many2one('account.journal', 'Diario', required=True)

    def crear_contrapartida(self):
        pago_id = self.env.context.get('active_ids', [])[0]
        pago = self.env['account.payment'].browse(pago_id)

        if not pago.cuenta_transitoria_id:
            raise UserError('La cuenta transitoria no está definida para este pago.')

        if pago.payment_type == 'inbound':
            move_line = self.env['account.move.line'].search([('payment_id', '=', pago_id), ('credit', '>', 0)])
            monto = move_line.credit
            credit1 = 0
            debit1 = monto
            credit2 = monto
            debit2 = 0
        elif pago.payment_type == 'outbound':
            move_line = self.env['account.move.line'].search([('payment_id', '=', pago_id), ('debit', '>', 0)])
            monto = move_line.debit
            credit1 = monto
            debit1 = 0
            credit2 = 0
            debit2 = monto

        dict = {}
        dict['date'] = fields.Datetime.now()
        sequence_id = self.env['ir.sequence'].search([('name','like', self.diario_id.name)])
        dict['name'] = sequence_id.with_context(sequence_date=pago.date).next_by_id()
        dict['partner_id'] = pago.partner_id.id
        dict['ref'] = pago.ref or ''
        dict['journal_id'] = self.diario_id.id
        #dict['amount'] = monto
        dict['state'] = 'draft'

        lineas = []
        lineas.append((0, 0, {
            'name': '/',
            'partner_id': pago.partner_id.id,
            'journal_id': self.diario_id.id,
            'account_id': move_line.account_id.id,
            'credit': credit1,
            'debit': debit1,
            #'state': 'draft',
        }))
        lineas.append((0, 0, {
            'name': '/',
            'partner_id': pago.partner_id.id,
            'journal_id': self.diario_id.id,
            'account_id': self.cuenta_destino_id.id,
            'credit': credit2,
            'debit': debit2,
            #'state': 'draft',
        }))
        dict['line_ids'] = lineas

        move = self.env['account.move'].create(dict)
        move.post()

        return {'type': 'ir.actions.act_window_close'}
    