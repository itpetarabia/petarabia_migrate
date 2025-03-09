# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "POS Fixed Amount Discount",
    "summary": "fixed amount discount option along with the percentage",
    "version": "14.0.1.0.1",
    "category": "Point of Sale",
    "website": "https://www.mast-it.com",
    "author": "Mast-IT Bahrain",
    "application": True,
    "installable": True,
    "depends": [
        "pos_discount","point_of_sale"
    ],
    'images': ['static/description/cover_picture.png'],
    "data": [
        "views/pos_templates.xml",
        "views/pos_view.xml",

    ],
    "qweb": [
        'static/src/xml/discount_templates.xml',
    ]
}
