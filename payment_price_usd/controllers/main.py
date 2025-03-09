# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import UserError


class WebsiteSaleDelivery(WebsiteSale):


    def _update_website_sale_delivery_return(self, order, **post):
        print("order==", order, order.amount_total_usd)
        Monetary = request.env['ir.qweb.field.monetary']
        currency_ussd = order.currency_usd
        res = super(WebsiteSaleDelivery, self)._update_website_sale_delivery_return(order, **post)
        if order:
            res['new_amount_total_usd'] = Monetary.value_to_html(order.amount_total_usd, {'display_currency': currency_ussd})
        print("res===", res)
        return res

