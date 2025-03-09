# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    is_cross_selling = fields.Boolean('Cross Selling', default=False)


    
    """def get_cross_selling_products(self, product_id,pricelist_id):
        
        pos_cross_product_ids = self.env['product.product'].search([('id', '=', product_id)]).accessory_product_ids
        vals = []
        for rec in pos_cross_product_ids:
            pricelist_price = rec.with_context(pricelist=pricelist_id, uom=rec.uom_id.id).price
            #pricelist_price_str = f'%.{rec.product_id.cost_currency_id.decimal_places}f' % pricelist_price
            pricelist_price = round(pricelist_price, rec.cost_currency_id.decimal_places)

            vals.append({
                'id': rec.id,
                'image': '/web/image?model=product.product&field=image_128&id='
                         + str(rec.id),
                'name': rec.name,
                'symbol': rec.cost_currency_id.symbol,
                #'price': rec.product_id.lst_price,
                'price': pricelist_price,
                #'pricelist_price_str': pricelist_price_str,
                'selected': False})
        return vals"""

