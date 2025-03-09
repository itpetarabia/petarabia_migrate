from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # def _search_qty_available_new(self, *args, **kw):
    #     if self.env.context.get('hide_unavailable_prods'):
    #         self = self.sudo()
    #     return super(Product, self)._search_qty_available_new(*args, **kw)
    @api.model
    def search(self, args, **kw):
        if self.env.context.get('hide_unavailable_prods'):
            website = self.env['website'].get_current_website()
            if self.env.user.has_group('base.group_public'):
                args += [('website_published', '=', True)]
            args += [('qty_available', '>', 0.0)]
            self = self.sudo().with_context(warehouse=website._get_warehouse_available())
        return super(ProductTemplate, self).search(args, **kw)


# class Warehouse(models.Model):
#     _inherit = 'stock.warehouse'

#     @api.model
#     def check_access_rights(self, *args, **kw):
#         if args[0] == 'read' and self.env.context.get('hide_unavailable_prods'):
#             return
#         return super(Warehouse, self).check_access_rights(*args, **kw)

# class Location(models.Model):
#     _inherit = 'stock.location'

#     @api.model
#     def check_access_rights(self, *args, **kw):
#         if args[0] == 'read' and self.env.context.get('hide_unavailable_prods'):
#             return
#         return super(Location, self).check_access_rights(*args, **kw)

# class Quant(models.Model):
#     _inherit = 'stock.quant'

#     @api.model
#     def check_access_rights(self, *args, **kw):
#         if args[0] == 'read' and self.env.context.get('hide_unavailable_prods'):
#             return
#         return super(Quant, self).check_access_rights(*args, **kw)