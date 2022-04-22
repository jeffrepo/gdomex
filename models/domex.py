# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class Color(models.Model):
    _name = 'domex.color'

    name = fields.Char("Nombre")