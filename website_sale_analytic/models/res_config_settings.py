from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', related='website_id.analytic_account_id', readonly=False)