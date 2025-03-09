{
    'name': "Stock ledger report",
    'version': '14.0.1.0',
    'category': 'Sales/Sales',
    'summary': """Stock ledger report""",
    'description': """
        Stock ledger report
    """,

    'author': 'Isa AlDoseri',
    'depends': ['point_of_sale', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'reports/reports.xml',
        'views/stock_ledger_wizard.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
