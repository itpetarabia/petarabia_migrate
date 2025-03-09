# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'POS backend print receipt',
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Mast-IT Bahrain',
    'sequence': 6,
    'summary': 'POS backend print receipt',
    'description': """

This module for re print POS receipt in backend
.

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_receipt_templates.xml',
        'report/pos_receipt_templates.xml',
        'report/pos_receipt_reports.xml',
        'views/pos_order_view.xml',

    ],
    #'qweb': ['static/src/xml/pos_receipt.xml'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
