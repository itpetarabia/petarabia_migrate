# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Rename Addresses',
    'summary': 'Rename fields on addresses',
    'sequence': '19',
    'author': 'Mast-IT Bahrain',
    'version': '14.0.2.0.0',
    'category': 'Base',
    'complexity': 'easy',
    'description': """
Extended Addresses Management
=============================

Coming Soon.
        """,
    'data': [
        'views/base_address_extended.xml',
        'views/sale_views.xml',
        'data/base_address_extended_data.xml',
        'data/data.xml',
'data/res_partner_data.xml',
        'views/templates.xml',
        'views/pos_templates.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'depends': ['base_address_extended', 'sale', 'website_sale', 'point_of_sale'],
}
