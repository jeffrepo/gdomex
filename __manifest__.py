# -*- coding: utf-8 -*-
{
    'name': "GDOMEX",

    'summary': """ Módulo de GDOMEX """,

    'description': """
         Módulo para GDOMEX
    """,

    'author': "",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['stock','project'],

    'data': [
        'views/stock_quant_views.xml',
        'views/stock_production_lot_views.xml',
        'security/ir.model.access.csv',
    ],
}
