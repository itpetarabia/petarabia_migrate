# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Order to POS Payment Methods',
    'version' : '1.0',
    'summary': 'Setting a priority to payment methods',
    'sequence': 4,
    'description': "Helpful to sort the payment methods by priority",
    'category': 'POS',
    'website': 'https://www.github.com/itpetarabia/custom-modules',
    'license': 'LGPL-3',
    'depends' : ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
        'views/pos_assets.xml',

    ],
    'demo': [],
    'qweb': [],

    'installable': True,
    'application': False,
    'auto_install': False,
}
