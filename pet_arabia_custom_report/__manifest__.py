# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'Pet Arabia Customized Reports',
    'version': '1.1',
    'author': 'Mast-IT Bahrain',
    'category': 'Invoices & Payments',
    'summary': 'Pet Arabia Customized Reports',
    'description': """
This module for modify reports.
    """,
    'depends': ['account','sale','purchase','iban_partner_bank'
                 ],
    'data': [
        'data/report_paperformat_data.xml',
        'report/report_invoice.xml',
        'report/invoice_delivery_note.xml',
        'report/report_payment_receipt_templates.xml',
        'report/report.xml',
        'views/stock_views.xml',
        'report/sale_report_templates.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True
}

