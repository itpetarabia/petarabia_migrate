# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Allow POS Refund',
    'version': '14.0.0.1',
    'category': 'Point of sale',
    'author':'Mast Information Technology - Bahrain',
    'description': "Allow pos refund and payment for users, from back office. Ticket # 1445",
    'depends': ['point_of_sale'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'security/ir.model.access.csv',
             ],
    'installable': True,
}
