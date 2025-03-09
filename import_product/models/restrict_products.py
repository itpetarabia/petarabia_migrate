from odoo import api, models
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('import_product.group_import_product'):
            raise ValidationError('Only Pet Arabia Administrators can create products!')
        return super().create(vals_list)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('import_product.group_import_product'):
            raise ValidationError('Only Pet Arabia Administrators can create products!')
        return super().create(vals_list)