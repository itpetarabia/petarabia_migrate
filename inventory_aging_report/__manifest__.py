# -*- coding: utf-8 -*-
{
    'name': 'Inventory Aging Report (Excel)',
    'version': '15.0.0.1',
    'category': 'Inventory',
    'author': 'Mast Information Technology - Bahrain',
    'description': "Ticket # 1208",
    'license': 'LGPL-3',
    'depends': ['report_xlsx', 'stock_account','purchase_stock','product_expiry'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'report/report.xml',
            'wizard/inv_aging_rpt_wiz_views.xml',
            'security/ir.model.access.csv',
             ],
    'installable': True,
}
