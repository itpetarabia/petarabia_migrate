{
    'name': "Send SMS",
    'version': '14.0.2.0.0',
    'author': "Mast-IT Bahrain",
    'category': 'Tools',
    'summary':'Allows you to send SMS to the mobile no.',
    'description':'Allows you to send SMS to the mobile no.',
    'depends': ['base', 'calendar', 'pets_data', 'appointments', 'pos_loyalty_ext'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/service_send_appointment_sms.xml',
        'views/sms_messages_view.xml' 
    ],
    'license': 'LGPL-3',
    'installable':True,
    'auto_install':False,
    'application':True,
}
# Change log

# 14.0.2 -> 26th Oct 2023: removed the viewable and editable API keys, URL and USER after moving to etisalcom. The credentials are stored in the odoo.conf file