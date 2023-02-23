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
        'data/report_paperformat_data.xml',
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
        'views/product_views.xml',
        'views/account_analytic_view.xml',
        'views/report.xml',
        'views/report_saleordershipping_domex.xml',
        'views/report_so_almex.xml',
        'views/report_so_domex.xml',
        'views/report_so_aplytek.xml',
        'report/report_envio_domex.xml',
        'report/report_envio_aplytek.xml',
        'report/report_stockpicking_domex.xml',
        'report/report_envio_almex.xml',
        'report/report_orden_trabajo.xml'
    ],
}
