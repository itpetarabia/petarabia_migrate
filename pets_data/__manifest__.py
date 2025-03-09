# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Pets',
    'version' : '1.0',
    'summary': 'Managing Pet Database',
    'sequence': 4,
    'description': "=====",
    'category': 'Pet',
    'website': 'https://www.github.com/itpetarabia/custom-modules',
    'license': 'LGPL-3',
    # you got to download report_xlsx from Odoo app store
    'depends' : ['mail', 'base', 'point_of_sale'],
    'data': [
        # Security 1st
        'security/ir.model.access.csv',
        # Data Files 2nd
        'data/data.xml',
        # Wizard 3rd

        # Views 4th
        'views/pet_view.xml',
        'views/pet_type_view.xml',
        'views/customer_pets_view.xml',
        'views/menu.xml',

        # Reports Templates 5th
        # 'report/all_patient_list.xml',

        # Reports 6th
        # 'report/report.xml',
    ],
    'demo': [],
    'qweb': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
