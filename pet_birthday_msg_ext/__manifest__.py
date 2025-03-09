{
    'name': "SMS Birthday Message",
    'version': '14.0.0.0.0',
    'author': "Isa AlDoseri",
    'category': 'SMS',
    'summary':'Allows us to send birthday wishes to customers pets!',
    'depends': ['base', 'pets_data', 'send_sms_ext'],
    'data': [
        'data/bday_sms_cron.xml'
    ],
    'license': 'LGPL-3',
    'installable':True,
    'auto_install':False,
    'application':False,
}
