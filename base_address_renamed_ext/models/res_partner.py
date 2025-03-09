# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # @api.model
    # def create_from_ui(self, partner):

    #     if partner.get('city_id'):
    #         partner['city_id'] = int(partner['city_id'])
    #     print("partner==", partner)
    #     return super(ResPartner, self).create_from_ui(partner)

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False
