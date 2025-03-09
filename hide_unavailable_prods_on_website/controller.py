from odoo.addons.website_sale.controllers.main import WebsiteSale


from odoo import http
from odoo.http import request
from odoo.osv import expression

class CustomWebsiteSale(WebsiteSale):
    # def __init__(self, *args, **kw):
    #     super(CustomWebsiteSale, self).__init__(*args, **kw)

    @staticmethod
    def _add_context_for_unavailable_products(request):
        ctx = request.context.copy()
        ctx.update(hide_unavailable_prods=True)
        request.context = ctx

    # def _get_search_domain(self, *args, **kw):
    #     subdomains = super()._get_search_domain(*args, **kw)
    #     # To remove all products that are out-of-stock
    #     domains = []
    #     domains.append(subdomains)
    #     domains.append([('qty_available', '>', 0.0)])
    #     return expression.AND(domains)

    @http.route()
    def shop(self, *args, **kw):
        self._add_context_for_unavailable_products(request)
        return super(CustomWebsiteSale, self).shop(*args, **kw)


    @http.route()
    def products_autocomplete(self, *args, **kw):
        self._add_context_for_unavailable_products(request)
        return super(CustomWebsiteSale, self).products_autocomplete(*args, **kw)
    
    @http.route('/json/shop/product/', type='json', auth='public', website=True, sitemap=False)
    def get_next_product(self, *args, **kw):
        self._add_context_for_unavailable_products(request)
        return super(CustomWebsiteSale, self).get_next_product(*args, **kw)