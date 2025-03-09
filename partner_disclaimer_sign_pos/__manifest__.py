# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Customer Disclaimer Sign - POS',
    'version': '14.0.0.1',
    'category': 'Point of sale',
    'author':'Mast Information Technology - Bahrain',
    'description': "Coming Soon",
    'depends': ['point_of_sale','partner_disclaimer_sign'],
    'website': 'http://www.mast-it.com',
    'data': [
            'views/templates.xml',
             ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/*.xml'],
    
}
