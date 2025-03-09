# -*- coding: utf-8 -*-

{
    'name': 'POS Cross-Selling',
    'version': '14.0.1.0.1',
    'category': 'Point Of Sale',
    'sequence': '20',
    'summary': 'Ticket - Cross Selling in point of sale (#2243,#2244)',
    'description': "This module is used for cross selling products in pos. "
                   "We can manage and use the cross-selling product",
    'author': 'Mast-IT Bahrain',
    'website': 'https://www.mast-it.com',
    'depends': ['point_of_sale','report_xlsx','website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_templates.xml',
        'wizard/pos_cross_selling.xml',
        'report/point_of_sale_report.xml',
    ],
    'qweb': [
        #'static/src/xml/CrossProducts.xml',
        'static/src/xml/Orderline.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
