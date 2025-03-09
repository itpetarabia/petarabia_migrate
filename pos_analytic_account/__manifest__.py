{
    'name': 'POS Analytic Account',
    'version': '14.0.0.1',
    'category': 'Point Of Sale',
    'author': 'Mast Information Technology - Bahrain',
    'summary': "analytic account for pos order and accounting entries",
    'depends': ['point_of_sale'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'views/pos_config_views.xml',
            'views/pos_order_views.xml',
             ],
    'installable': True,
    'qweb': ['static/src/xml/*.xml'],
}