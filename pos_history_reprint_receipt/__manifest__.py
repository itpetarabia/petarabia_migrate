# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'POS History Reprint Receipt',
    'version': '14.0.1.0.1',
    'category': 'Point of Sale',
    'summary': 'Customize POS history reprint receipt',
    'author': 'Mast-IT Bahrain',
    'description': """
Coming soon.
    """,
    'depends': ['pos_orders_history_reprint','point_of_sale_receipt_ext'],
    'data': [
            'views/point_of_sale.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'qweb': ['static/src/xml/pos.xml'],
}

