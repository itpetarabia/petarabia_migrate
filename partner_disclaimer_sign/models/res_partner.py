from odoo import models,fields

class ResPart(models.Model):
    _inherit = 'res.partner'

    disclaimer_sign = fields.Boolean()
    disclaimer_sign_doc = fields.Binary("Disclaimer Sign Document",attachment=True)

