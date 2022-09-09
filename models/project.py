# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import api, fields, models, _, _lt
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.osv.query import Query
import logging

class Project(models.Model):
    _inherit = 'project.project'

    transferencias_ids = fields.One2many('stock.picking', 'project_id', string='Transferencias')

    def activar_envio(self):
    	view_id = self.env.ref('stock.view_picking_form').id
    	context = self._context.copy()
    	return {
            'name':'form_name',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'stock.picking',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':self.id,
            'target':'new',
            'context':context,
        }
