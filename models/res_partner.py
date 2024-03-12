# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError

import logging

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        if vals_list:
            for val in vals_list:
                if 'vat' in val and val['vat']:
                    partner_id = self.env['res.partner'].search([('vat', '=', val['vat'])])
                    if len(partner_id) > 0:
                        raise ValidationError(_('El contacto con el NIT '+ str(val['vat']) + ' ya existe' ))
        res = super(ResPartner, self).create(vals_list)
        return res

    # def write(self, vals):
    #     for partner in self:
    #         logging.warning('self')
    #         logging.warning(partner)
    #         if vals.get('vat'):
    #             logging.warning(vals)
    #             partner_id = self.env['res.partner'].search([('vat', '=', vals['vat']),('id','!=', self.id)])
    #             logging.warning('partner_id')
    #             logging.warning(partner_id)
    
    #         res = super(ResPartner, self).write(vals)
    #         logging.warning('res')
    #         logging.warning(res)
    #     if len(partner_id) > 0:
    #         raise ValidationError(_('El contacto con el NIT '+ str(vals['vat']) + ' ya existe' ))
    #     return result