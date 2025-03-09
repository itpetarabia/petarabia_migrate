# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'POS Top20 Customer Report',
    'version': '1.0',
    'category': 'Point Of Sale',
    'summary': 'Report Ext v12.0',
    'author': 'Mast',
    'description': """
This module for Top 20 POS customer reports.
    """,
    'depends': ['report_xlsx', 'point_of_sale'],
    'data': [
        'report/report_views.xml',
        'report/report.xml',
        'security/ir.model.access.csv',

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

