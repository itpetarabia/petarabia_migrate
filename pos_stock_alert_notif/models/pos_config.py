from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id"
    )
    out_stock_alert = fields.Boolean("Out of stock alert", related='company_id.pos_out_stock_alert', store=True)
    out_stock_notif = fields.Boolean("Out of stock notification by email", default=True,related='company_id.pos_out_stock_notif', store=True)
    out_stock_notif_user_ids = fields.Many2many('res.users',related='company_id.pos_out_stock_notif_user_ids',string="Out of stock notify")

    stock_load_background = fields.Boolean(default=True)
    limited_stock = fields.Integer(default=300)

    def get_most_selling_products_ordered(self,product_ids_all=[]):
        query = """
                WITH pm AS (
                      SELECT product_id,
                             Max(write_date) date
                        FROM stock_quant
                    GROUP BY product_id
                )
                   SELECT p.id
                     FROM product_product p
                LEFT JOIN product_template t ON product_tmpl_id=t.id
                LEFT JOIN pm ON p.id=pm.product_id
                    WHERE (t.company_id=%(company_id)s OR t.company_id IS NULL) 
                    AND t.type = 'product'
                    AND p.id IN %(product_ids)s
                 ORDER BY COALESCE(pm.date,p.write_date) DESC    
            """
        params = {
            'company_id': self.company_id.id,
            'product_ids': tuple(product_ids_all+[0])
        }
        self.env.cr.execute(query, params)
        product_ids = []
        res = self.env.cr.fetchall()
        if res:
            product_ids = [p[0] for p in res]
        #products = self.env['product.product'].search_read([('id', 'in', product_ids)], fields=fields)
        return product_ids
