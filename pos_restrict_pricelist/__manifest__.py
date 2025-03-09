# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'POS Restrict Change Pricelist in Point of sale',
    'version': '1.1',
    'category': 'pos',
    'summary': 'Restrict Change Pricelist in Point of sale for cashier ',
    'author': 'Mast-IT Bahrain',
    'description': """
Coming soon.
    """,
    'depends': ['point_of_sale'],
    'data': [
        'security/security.xml',
        'views/pos_templates.xml',
        'views/pos_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

