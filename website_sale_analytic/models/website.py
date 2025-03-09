from odoo import models, fields

class Website(models.Model):
    _inherit = 'website'

    analytic_account_id = fields.Many2one('account.analytic.account')

    def _prepare_sale_order_values(self, partner, pricelist):
        self.ensure_one()
        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)
        if self.analytic_account_id:
            values['analytic_account_id'] = self.analytic_account_id.id
        return values
