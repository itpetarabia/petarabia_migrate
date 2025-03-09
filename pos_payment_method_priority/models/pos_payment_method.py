from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"
    _order = 'priority asc, name asc'
    priority = fields.Integer(string='Priority', default=100, help='Decides which payment method shows up first in the POS session.')
