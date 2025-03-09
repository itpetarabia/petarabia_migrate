# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.addons.website_sale.controllers.main import WebsiteSale



class base_address_renamed_extWebsiteSale(WebsiteSale):
    def _get_mandatory_fields_billing(self, country_id=False):
        req = super()._get_mandatory_fields_billing(country_id)

        new_req = []
        if 'state_id' in req: new_req += ['state_id']
        if 'zip' in req: new_req += ['zip']

        new_req += ['name', 'email', 'street_number', 'street2', 'country_id']
        return new_req


    def _get_mandatory_fields_shipping(self, country_id=False):
        req = super()._get_mandatory_fields_shipping(country_id)

        new_req = []
        if 'state_id' in req: new_req += ['state_id']
        if 'zip' in req: new_req += ['zip']

        new_req += ['name', 'phone', 'street_number', 'street2', 'country_id']

        return new_req