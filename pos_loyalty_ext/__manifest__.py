# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'POS Loyalty Ext',
    'version': '1.1',
    'category': 'pos',
    'summary': 'Exclude payment methods from calculate in Loyalty',
    'author': 'Mast-IT Bahrain',
    'description': """
Coming soon.
    """,
    'depends': ['pos_loyalty', 'point_of_sale', 'product'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/pos_loyalty_templates.xml',
    ],
    'qweb': [
        'static/src/xml/PointsCounter.xml',
        'static/src/xml/OrderReceipt.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

