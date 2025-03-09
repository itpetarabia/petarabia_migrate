from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_pos_product_quantity_available(self,location_id,lot_ids=[],lot_names=[],fetch_lot=True):
        #rint('get_pos_product_quantity_available=',lot_ids,lot_names,fetch_lot)
        lot_ids = [int(lot_id) for lot_id in lot_ids]
        obj_spl = self.env['stock.production.lot']
        to_return = {}
        for rec in self:
            to_return.setdefault(rec.id,{})
            to_return[rec.id]['qty_available'] = rec.with_context(location=location_id).qty_available
            if not fetch_lot or \
            rec.tracking == 'none' or \
            (to_return[rec.id]['qty_available'] <= 0 and not lot_names and not lot_ids):
                continue
            domain_lots = [('product_id','=',rec.id)]
            not lot_names and lot_ids and domain_lots.append(('id','in',lot_ids))
            not lot_ids and lot_names and domain_lots.append(('name','in',lot_names))
            if lot_ids and lot_names:
                domain_lots += ['|',('id','in',lot_ids),('name', 'in', lot_names)]
            if not lot_ids and not lot_names:
                #available qty lots only - to improve speed
                domain_lots += [('quant_ids','!=',False)]
                lots = obj_spl.search(domain_lots).filtered(lambda l: l.product_qty > 0)
                #rint("lots=",lots,domain_lots,rec.name)
            else:
                lots = obj_spl.search(domain_lots)
                #rint("fecthing lots=",lots)
            for lot in lots:
                to_return[rec.id][lot.id] = {'qty_available': rec.with_context(location=location_id, lot_id=lot.id).qty_available,'name': lot.name}
        return to_return