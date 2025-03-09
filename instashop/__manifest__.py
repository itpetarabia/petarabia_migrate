# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Instashop',
    'version' : '14.0',
    'summary': 'Updating product stock with Instashop',
    'sequence': 3,
    'category': 'Point of Sale/Instashop',
    'website': 'https://www.github.com/itpetarabia/custom-modules',
    'license': 'LGPL-3',
    'depends' : ['point_of_sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/config_view.xml',
        'views/product_view.xml',
        'views/pos_instashop_view.xml',
        'views/menu.xml',
        'data/cron_update_insta_job.xml',
    ],
    'demo': [],
    'qweb': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
