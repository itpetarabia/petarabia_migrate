# Copyright 2014-2019 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
# Copyright 2015 Bassirou Ndaw <https://github.com/bassn>
# Copyright 2015 Alexis de Lattre <https://github.com/alexis-via>
# Copyright 2016-2017 Stanislav Krotov <https://it-projects.info/team/ufaks>
# Copyright 2017 Ilmir Karamov <https://it-projects.info/team/ilmir-k>
# Copyright 2017 Artyom Losev
# Copyright 2017 Lilia Salihova
# Copyright 2017-2018 Gabbasov Dinar <https://it-projects.info/team/GabbasovDinar>
# Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# License MIT (https://opensource.org/licenses/MIT).

{
    "name": "POS: Prepaid credits",
    "summary": "Comfortable sales for your regular customers. Debt payment method for POS",
    "category": "Point Of Sale",
    "images": ["images/debt_notebook.png"],
    "version": "13.0.5.3.2",
    "author": "Mast-IT Bahrain",
    "website": "https://mast-it.com/",
    "external_dependencies": {"python": [], "bin": []},
    "depends": ["point_of_sale"],
    "data": [
        "security/pos_debt_notebook_security.xml",
        "data/product.xml",
        "views/pos_debt_report_view.xml",
        "views.xml",
        "views/pos_credit_update.xml",
        #"wizard/pos_credit_invoices_views.xml",
        #"wizard/pos_credit_company_invoices_views.xml",
        "data.xml",
        "security/ir.model.access.csv",
    ],
    "qweb": ["static/src/xml/pos.xml"],
    "demo": ["data/demo.xml"],
    "installable": True,
    "uninstall_hook": "pre_uninstall",
    "demo_title": "POS Debt/Credit Notebook",
    "demo_addons": [],
    "demo_addons_hidden": [],
    "demo_url": "pos-debt-notebook",
    "demo_summary": "Comfortable sales for your regular customers.",
    "demo_images": ["images/debt_notebook.png"],
}
