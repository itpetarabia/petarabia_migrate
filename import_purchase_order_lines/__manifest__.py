# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Import Purchase Order Lines from Excel or CSV File in odoo',
    'version': '14.0.0.4',
    'summary': 'Import purchase order line Data App for import purchase order lines import purchases data import PO line excel import purchase order line from excel import purchase order line from csv import mass purchase order import bulk purchase order line import',
    'description': """
	BrowseInfo developed a new odoo/OpenERP module apps.
	This module use for 
    odoo import bulk purchase Order lines from Excel file Import purchase order lines from CSV or Excel file.
	odoo Import purchases Import purchase order line Import purchase lines Import PO Line purchase Import Add PO from Excel import odoo
    odoo Add Excel Purchase order lines Add CSV file Import Purchase data Import excel file odoo
        Import stock with Serial number import
    Import stock with lot number import
    import lot number with stock import
    import serial number with stock import
    import lines import
    odoo import order lines import
    odoo import orders lines import
    import so lines import
    imporr po lines import
    import invoice lines import
    import invoice line import
Este módulo usa para importar compras a granel Ordem linhas do arquivo do Excel. Importar linhas de pedidos de compra a partir do arquivo CSV ou Excel.
Compra de importação, Importar linha de pedido de compra, Importar linhas de compra, Importar linha de pagamento. Compre Importação, Adicione PO a partir do Excel. Adicione as linhas de ordem de compra Excel. Adicione arquivo CSV. Dados de compra de importação. Importar arquivo excel

هذه الوحدة تستخدم لخطوط استيراد الشراء بالجملة من ملف إكسل. استيراد خطوط طلب الشراء من ملف CSV أو Excel.
استيراد المشتريات ، استيراد خط طلب الشراء ، خطوط شراء الواردات ، استيراد PO سطر. شراء استيراد ، إضافة أمر شراء من Excel.Add إكسل خطوط أمر الشراء. إضافة ملف CSV. استيراد بيانات الشراء. استيراد ملف اكسل
-
Ce module est utilisé pour importer des lignes de commande d'achat en gros à partir d'un fichier Excel. Importez des lignes de commande d'achat à partir d'un fichier CSV ou Excel.
Importer des achats, Importer une ligne de commande d'achat, Importer des lignes d'achat, Importer une ligne de commande. achat Importer, Ajouter un bon de commande depuis Excel.Ajouter Excel Lignes de commande d'achat.Ajouter un fichier CSV. Importer des données d'achat. Importer un fichier Excel

Este módulo se usa para la importación de compras a granel Ordene líneas desde el archivo de Excel. Importe líneas de orden de compra desde CSV o archivo de Excel.
Importar compras, Importar línea de orden de compra, Importar líneas de compra, Importar línea de pedido. comprar Importar, Agregar PO desde Excel. Agregar líneas de orden de compra de Excel. Agregar archivo CSV. Importar datos de compra. Importar archivo de Excel
-
	-
    """,
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    "price": 9,
    "currency": 'EUR',
    'category': 'Purchase',
    'depends': ['base','purchase'],
    'data': [   
                'security/ir.model.access.csv',
                'views/import_po_lines_view.xml',
                'data/attachment_sample.xml',
            ],
    'demo': [],
    'test': [],
    'installable':True,
    'auto_install':False,
    'application':True,
    'live_test_url':'https://youtu.be/VpiAemvzcpI',
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
