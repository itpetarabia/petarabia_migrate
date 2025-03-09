# Part of AktivSoftware See LICENSE file for full
# copyright and licensing details.
from odoo import models, api, _
from odoo.exceptions import UserError

class Res_Partner(models.Model):
    _inherit = "res.partner"

    @api.onchange('property_product_pricelist')
    def manage_pricelist_change(self):
        if self.property_product_pricelist and \
        not self.user_has_groups('sale_restrict_pricelist.groups_restrict_pricelist_change'):
            grp = self.env.ref('sale_restrict_pricelist.groups_restrict_pricelist_change')
            raise UserError(f"You don't have rights to change the Pricelist."
                            f"\nOnly '{grp.display_name}' users can change.\n\n"
                            f"User: {self.env.user.name}\n\n")