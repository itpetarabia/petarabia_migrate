from datetime import timedelta

from odoo import api, models, _

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    
    @api.onchange('expiration_date')
    def _onchange_autofill_other_date_fields(self):
        if self.expiration_date:
            self.removal_date = self.expiration_date - timedelta(days=15)
            self.alert_date = self.expiration_date - timedelta(days=150)
            self.use_date = self.expiration_date