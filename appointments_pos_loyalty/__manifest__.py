# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'Apply Loyalty point on appointments',
    'version': '14.0.1.0.1',
    'summary': 'Add loyalty point on POS order created by Appointment',
    'author': 'Mast-IT Bahrain',
    'description': """
Coming soon.
    """,
    'depends': ['appointments','pos_loyalty'],
    'data': [
            'views/pos_loyalty_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

