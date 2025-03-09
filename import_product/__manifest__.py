# -*- coding: utf-8 -*-
{
    'name': 'Import Products from Excel/CSV',
    'version': '14.0.0.4',
    'summary': 'Company Policy to upload products',
    'author': 'Isa AlDoseri',
    'category': 'Inventory',
    'depends': ['base','product','stock'],
    'data': [   
                'security/group.xml',
                'security/ir.model.access.csv',
                'views/import_product_view.xml',
                'data/attachment_sample.xml',
            ],
    'demo': [],
    'test': [],
    'installable':True,
    'auto_install':False,
    'application':True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
