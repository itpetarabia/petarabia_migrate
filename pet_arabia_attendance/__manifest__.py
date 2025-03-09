# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Pet Arabia Attendance',
    'version' : '14.0',
    'summary': 'Receives and Returns requests from the Pet Arabia Attendance App',
    'sequence': 3,
    'category': 'HR/Attendance',
    'website': 'https://www.github.com/itpetarabia/custom-modules',
    'license': 'LGPL-3',
    'depends' : ['mail', 'hr_attendance', 'auth_api_key'],
    'data': [
        'security/ir.model.access.csv',
        'views/registrations_view.xml',
        'views/locations.xml',
        'views/location_groups.xml',
        'views/hr_employee.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'qweb': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
