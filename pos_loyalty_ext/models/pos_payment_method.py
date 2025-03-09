# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models

class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    payment_method_loyal_ext = fields.Boolean(default=False, string='Exclude Payment Methods')

class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    pricelist_loyal_ext = fields.Boolean(default=False, string='Exclude Pricelist')