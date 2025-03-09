# -*- coding: utf-8 -*-

from odoo import fields, models

class CustomWebsite(models.Model):
    _inherit = 'website'

    shop_infinite_scrolling = fields.Boolean(string="Infinite Scrolling", default=True)

    def get_website_faq_list(self):
        faqs = self.env['faq'].sudo().search([('website_id', 'in', (False, self.get_current_website().id)),
        ('is_published', '=', True)])
        return faqs

class ShopInfiniteScrolling(models.TransientModel):
    _inherit = "res.config.settings"

    shop_infinite_scrolling = fields.Boolean(string="Infinite Scrolling",
        related='website_id.shop_infinite_scrolling', readonly=False)