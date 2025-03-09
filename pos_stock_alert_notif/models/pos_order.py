from odoo import models, fields, api
from .. import user_tz_dtm

class PosOrderOutStockLine(models.Model):
    _name = 'pos.order.out.stock.line'
    _description = 'POS Order Out of Stock Line'

    order_id = fields.Many2one('pos.order',string='Pos Order',ondelete='cascade',required=True)
    product_id = fields.Many2one('product.product',required=True,ondelete='cascade')
    lot_name = fields.Char("Lot / Serial (Unknown)")
    lot_id = fields.Many2one('stock.production.lot',string="Lot/Serial")
    qty_available = fields.Float(digits="Product Unit of Measure")
    qty_required = fields.Float(digits="Product Unit of Measure")
    qty_difference = fields.Float(digits="Product Unit of Measure",compute="_compute_qty_difference",store=True)

    @api.depends('qty_available','qty_required')
    def _compute_qty_difference(self):
        for rec in self:
            rec.qty_difference = rec.qty_available - rec.qty_required

class PosOrder(models.Model):
    _inherit = 'pos.order'

    out_stock_line = fields.One2many('pos.order.out.stock.line','order_id',string='Out of stock lines')
    out_stock_location_id = fields.Many2one('stock.location')
    out_stock_email_sent = fields.Boolean()

    #cron
    def send_out_stock_email(self):
        records = self.search([('out_stock_email_sent', '=', False),
                               ('out_stock_line', '!=', False)])
        if records:
            records.notify_out_stock_email()
            records.write({'out_stock_email_sent': True})

    def get_stock_alert_notif_partner_to_email(self):
        return ",".join(str(p) for p in self.config_id.out_stock_notif_user_ids.mapped('partner_id.id'))

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(PosOrder, self)._process_order(order, draft, existing_order)
        obj_osl = self.env['pos.order.out.stock.line']
        pos_order = self.browse(order_id)
        existing_order and pos_order.out_stock_line.unlink()
        #print("order['data']=",order['data'].get('out_stock_list'))
        for l in order['data'].get('out_stock_list',[]):
            l['order_id'] = order_id
            l['lot_id'] = l.get('lot_id',False) and int(l['lot_id']) or False
            obj_osl.create(l)
        pos_order.out_stock_line and pos_order.write({'out_stock_location_id': pos_order.config_id.default_location_src_id.id})
        #send email//hided may be make loading isssue in frontend (moved to cron job)
        #pos_order.notify_out_stock_email()
        return order_id

    def _get_is_module_installed(self,module_name):
        qry = f"select state from ir_module_module where name='{module_name}' and state ='installed'"
        self.env.cr.execute(qry)
        qry_res = self.env.cr.dictfetchall()
        if qry_res:
            return True
        return False

    def notify_out_stock_email(self):
        is_pos_hr_installed = self._get_is_module_installed("pos_hr")
        for rec in self:
            config = rec.config_id
            if not rec.out_stock_line or \
            not config.out_stock_notif_user_ids or \
            not config.out_stock_alert or \
            not config.out_stock_notif:
                continue
            sales_person = rec.user_id.name
            #if pos hr installed
            if is_pos_hr_installed and \
            rec.employee_id:
                sales_person = rec.employee_id.name
            rec = rec.with_context(date_order_str=user_tz_dtm.get_tz_date_time_str(rec,rec.date_order),sales_person=sales_person)
            mt = rec.env.ref('pos_stock_alert_notif.email_template_pos_order_out_stock')
            mt.send_mail(rec.id, force_send=True)