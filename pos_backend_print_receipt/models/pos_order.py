# -*- coding: utf-8 -*-
import logging
from . import user_tz_dtm

from odoo import api, fields, models, tools, _
from functools import partial
from odoo.tools.misc import formatLang
import urllib
import json
import requests
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"
    _description = "Point of Sale Orders"

    def re_print_receipt(self):
        print("re_print_receipt")
        self.ensure_one()
        return self.env.ref('pos_backend_print_receipt.report_pos_receipt_backend').report_action(self)

    def change_size_page(self, items):
        paper_format = self.env['report.paperformat'].search(
            [('id', '=', self.env.ref('pos_backend_print_receipt.paperformat_backend_pos_receipt').id)])
        if len(items) > 7:
            paper_format.sudo().page_height = 200 + (len(items) * 10)
        else:
            paper_format.sudo().page_height = 220

    def get_extra_values(self,which):
        vals = {}
        if which == "date_order":
            rec_dates = []
            rec_days = []
            rec_times = []
            rec_dates.append(user_tz_dtm.get_date_str(self,self.date_order))
            rec_days.append(user_tz_dtm.get_tz_date_time(self, self.date_order).strftime("%A"))
            rec_times.append(user_tz_dtm.get_tz_date_time(self, self.date_order).strftime("%I:%M:%S %p"))
            vals.update({'dates':",".join(rec_dates),
                         'days': ",".join(rec_days),
                         'times': ",".join(rec_times)
                         })
        return vals

    def get_total_discount(self):
        sum = 0
        for order in self:
            for line in order.lines:
                sum = sum + (line.price_unit * (line.discount / 100) * line.qty)
        return sum

    def get_total_payment(self):
        payment = {}
        for order in self:
            for line in order.payment_ids:
                if line.payment_method_id:
                    if line.payment_method_id not in payment:
                        payment.update({line.payment_method_id: 0})
                    payment[line.payment_method_id] += line.amount
        sorted_d = sorted(payment.items(), key=lambda x: x[1])
        return sorted_d
