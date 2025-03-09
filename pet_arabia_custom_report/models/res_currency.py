from odoo import models

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def amount_to_str(self,amount=0):
        return f'%.{self.decimal_places}f' % amount