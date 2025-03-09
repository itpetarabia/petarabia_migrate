# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Custom Receipt',
    'version': '1.0.1',
    'category': 'Point Of Sale',
    'author':'Mast Information Technology - Bahrain',
    'summary': 'Dynamic POS Receipt',
    "images"               :  ['static/description/banner.png'],
    'description': """
	By using this module can make a custom receipt.
	""",
    'price': 5,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/point_of_sale.xml',
        'views/pos_config_view.xml'
    ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/pos.xml'],
    
}
