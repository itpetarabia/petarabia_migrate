# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class PhoneValidationMixin(models.AbstractModel):
    _name = 'phone.validation.mixin'
    _inherit = 'phone.validation.mixin'
    _description = 'Phone Validation (Delete Extra Spaces)'

    def phone_format(self, number, country=None, company=None):
        number = super().phone_format(number, country, company)
        number = number.replace(' ', '').replace('-', '')
        return number
