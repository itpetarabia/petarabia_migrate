{
    'name': 'Lot Disable Company Rule - 14',
    'version': '14.0.0.1',
    'category': 'Inventory',
    'author': 'Mast Information Technology - Bahrain',
    'summary': "Disable lot company rule",
    'depends': ['stock'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'security/stock_security.xml',
            'views/stock_production_lot_views.xml',
            'views/stock_move_views.xml',
             ],
    'installable': True,
    'qweb': ['static/src/xml/*.xml'],
}
