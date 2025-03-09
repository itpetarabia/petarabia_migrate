# -*- coding: utf-8 -*-

{
    'name': 'Save Card Ext',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 380,
    'summary': 'Checkbox to save the card if necessary, and be able to use the stored card later on when the customer tries to checkout for the 2nd time',
    'version': '1.0',
    'description': """Stripe Payment Acquirer""",
    'author': 'Mast-IT Bahrain',
    'depends': ['payment_stripe','payment'],
    'data': [
        'views/payment_templates.xml',
        'views/payment_views.xml',

    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,

}
