# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Hide Success Product Availability Messages',
    'category': 'Website/Website',
    'summary': 'Replace "X Unit(s) available" message against each product on the website, with nothing.',
    'description': """
Replace "X Unit(s) available" message against each product on the website, with nothing.
    """,
    'depends': [
        'website_sale_stock',
    ],
    'data' : [
        'views/asset.xml'
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
