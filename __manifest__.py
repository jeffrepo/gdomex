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

    'depends': ['stock','project', 'sale'],

    'data': [
        'views/stock_quant_views.xml',
        'views/stock_production_lot_views.xml',
        'views/account_report.xml',
        'report/reporte_cheque_axir_g_t.xml',
        'report/reporte_voucher_aplytek.xml',
        'report/reporte_inter_continuo.xml',
        'security/ir.model.access.csv',
        'views/account_payments_views.xml',
        'views/project_project_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_views.xml',
        'views/account_analytic_view.xml'
    ],
}
