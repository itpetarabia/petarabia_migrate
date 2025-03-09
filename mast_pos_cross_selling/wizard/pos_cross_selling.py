# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

#from dateutil.relativedelta import relativedelta
#from dateutil import relativedelta
#import pytz
from datetime import datetime

class PosCrossSellingDetails(models.TransientModel):
    _name = 'pos.cross.selling.wizard'
    _description = 'POS Cross Selling Details Report'



    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(required=True, default=fields.Datetime.now)
    pos_config_ids = fields.Many2many('pos.config', 'pos_cross_selling_configs',
        default=lambda s: s.env['pos.config'].search([]))

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def generate_report(self):
        #print("generate_report==========")
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids}
        return self.env.ref('mast_pos_cross_selling.action_report_cross_selling_xlx').report_action([], data=data)

    def get_report_values_cross_selling(self):
        #date_from = f"{self.start_date} 00:00:00"
        #date_to = f"{self.end_date} 23:59:59"
        #date_from1 = datetime.strptime(f"{self.start_date}", "%Y-%m-%d").date()
        #date_to1 = datetime.strptime(f"{self.end_date}", "%Y-%m-%d").date()
        domain = []
        domain.append(('date_order', '<', self.end_date))
        domain.append(('date_order', '>', self.start_date))
        if self.pos_config_ids:
            domain.append(('config_id', 'in', self.pos_config_ids.ids))
        orders = self.env['pos.order'].search(domain)
        data = []
        #print("orders====",orders)
        if orders:
            qry = """SELECT rp.name AS user_name , po.pos_reference  AS reference, SUM(pl.qty) AS quantity, SUM(pl.price_subtotal) AS Amount, pc.name AS config, po.id AS po_id
                                FROM  pos_order_line AS pl
                                INNER JOIN pos_order as po ON po.id = pl.order_id
                                LEFT JOIN res_users as ru ON ru.id = po.user_id
                                LEFT JOIN res_partner as rp ON rp.id = ru.partner_id
                                LEFT JOIN pos_session as ps ON ps.id = po.session_id
                                LEFT JOIN pos_config as pc ON pc.id = ps.config_id
                                    WHERE po.date_order >= '%s'
                                          AND po.date_order <= '%s'
                                          AND po.id in %s
                                          AND pl.is_cross_selling IS TRUE
                                          group by po.id,rp.name,pc.name
                                          ORDER BY po.pos_reference ASC
                                               """ % (self.start_date, self.end_date, tuple(orders.ids + [0]))
            self._cr.execute(qry)
            data = self._cr.dictfetchall()
        print("data======",data)
        return data