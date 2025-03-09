# Part of AktivSoftware See LICENSE file for full
# copyright and licensing details.
from odoo import models, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('pricelist_id')
    def manage_pricelist_change(self):
        if self.partner_id and \
        self.pricelist_id and \
        self.partner_id.property_product_pricelist.id != self.pricelist_id.id and \
        not self.user_has_groups('sale_restrict_pricelist.groups_restrict_pricelist_change'):
            grp = self.env.ref('sale_restrict_pricelist.groups_restrict_pricelist_change')
            raise UserError(f"You don't have rights to change the Pricelist."
                            f"\nOnly '{grp.display_name}' users can change.\n\n"
                            f"User: {self.env.user.name}\n\n")