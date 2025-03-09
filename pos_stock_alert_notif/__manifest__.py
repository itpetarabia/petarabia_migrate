{
    'name': 'POS Stock Alert & Notification',
    'version': '15.0.0.1',
    'category': 'Point Of Sale',
    'depends': ['point_of_sale'],
    'summary': 'pos stock alert and notifucation by email. Ticket # 1283',
    'author': 'Mast Information Technology - Bahrain',
    'data': [
        'views/templates.xml',
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        #'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
        'data/mail_data.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'qweb': [
        'static/src/xml/*.xml'
        ],
}
