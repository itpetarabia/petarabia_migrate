# -*- coding: utf-8 -*-


{
    'name': 'Hide Product Cost Price',
    'summary': """Product cost price is only visible to a specific group""",
    'version': '14.0.1.1.0',
    'description': """Product cost price is only visible to a specific group""",
    'author': 'Mast-IT Bahrain',
    'website': 'https://mast-it.com/',
    'category': 'Extra Tools',
    'depends': ['base', 'product','stock','stock_account'],
    'data': [
        'security/view_cost_price.xml',
        'views/hide_product_cost.xml'
    ],
    'images': ['static/description/hide_cost.png'],
    'installable': True,
    'auto_install': False,

}
