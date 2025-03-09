# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Loyalty Program Customize',
    'version': '1.0',
    'category': 'Point of Sale',
    'author': 'Mast-IT Bahrain',
    'sequence': 6,
    'summary': 'Loyalty Program for the Point of Sale ',
    'description': """

This module allows if you select rewards type as discount, then discount product price 
will be 'minimum points/ point cost'.

""",
    'depends': ['pos_loyalty'],
    'data': [
        'views/pos_loyalty_templates.xml'
    ],
    #'qweb': ['static/src/xml/loyalty.xml'],
    #'demo': [
    #    'data/pos_loyalty_demo.xml',
    #],
    'installable': True,
    'auto_install': False,

}
