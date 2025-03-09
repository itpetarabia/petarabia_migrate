# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Override Stripe Payment Errors',
    'version' : '1.0', # works with `payment_stripe` module v1
    'summary': 'The payment errors contain unwanted text, they will be overwritten',
    'sequence': 4,
    'category': 'Accounting/Payment Acquirers',
    'website': 'https://www.github.com/itpetarabia/custom-modules',
    'license': 'LGPL-3',
    'depends' : ['payment_stripe'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
