# -*- coding: utf-8 -*-

{
    'name': 'Change to USD Price',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 380,
    'summary': 'Change to USD Price at Checkout and BHD Prices all over the site for strip',
    'version': '1.0',
    'description': """Stripe Payment Acquirer""",
    'author': 'Mast-IT Bahrain',
    'depends': ['payment_stripe','website_sale', 'website_sale_delivery'],
    'data': [
        'views/website_price_usd_templates.xml',
        'views/templates.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,

}
