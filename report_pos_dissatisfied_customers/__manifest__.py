# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'POS Dissatisfied Customer Report',
    'version': '1.0',
    'category': 'Point Of Sale',
    'summary': 'Report Ext v12.0',
    'author': 'Mast-IT Bahrain',
    'description': """
This module for list dissatisfied customers.
    """,
    'depends': ['point_of_sale','report_xlsx'],
    'data': [
        'report/report_views.xml',
        'report/report.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

