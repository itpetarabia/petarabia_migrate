{
    'name': 'POS Cash Change To Same Payment Method - 14',
    'version': '14.0.0.1',
    'category': 'Point Of Sale',
    'author': 'Mast Information Technology - Bahrain',
    'summary': "If we have 2 cash PM. System add change to first (id asc). Through this module we add change to same PM (first cash transaction)",
    'depends': ['point_of_sale'],
    #'website': 'http://www.mast-it.com',
    'data': [

             ],
    'installable': True,
    'qweb': ['static/src/xml/*.xml'],
}