# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'Appointments',
    'version': '1.2',
    'summary': 'Coming Soon',
    'author': 'Mast',
    'description': """
This module for appointments.
    """,
    'depends': ['point_of_sale','calendar','product','hr', 'pets_data'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'security/multi_company_security.xml',
        'data/ir_sequence_data.xml',
        # 'data/fill_pets.xml',
        'views/res_config_settings_views.xml',
        'views/appointment_views.xml',
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}

