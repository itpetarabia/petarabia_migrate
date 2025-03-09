# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'Internal Transfer Request',
    'version': '14.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Allows user of one location to make request to another location',
    'author': 'Mast-IT Bahrain',
    'website': 'https://mast-it.com/',
    'description': """
Inventory Transfer Request
    """,
    'depends': ['stock'],
    'data': [
        'data/mail_data.xml',
        'data/reordering_req_data.xml',
        'security/reordering_security.xml',
        'security/ir.model.access.csv',
        'views/stock_view.xml',
        'views/reordering_req_views.xml',
    ],
    'images': ['static/description/cover_picture.png'],
    'installable': True,
    'auto_install': False,
    'application': True
}

