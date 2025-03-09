# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import user_tz_dtm

class PosDetails(models.TransientModel):
    _name = 'pos.top.customer.wizard'
    _description = 'Point of Sale Top 20 customer Report'

    user_id = fields.Many2one('res.users', string='User', index=True, tracking=True, default=lambda self: self.env.user)
    quantity = fields.Integer(string='Quantity', default=20, required=True)

    def generate_report(self):
        data = {}
        return self.env.ref('report_pos_top20_customer.pos_top20_customer_report').report_action([], data=data)

    def get_top20_customer(self):
        cr = self.env.cr
        query = 'SELECT c.name, c.phone, c.mobile, c.email, sum((p.qty * p.price_unit) * (100 - p.discount) / 100) as total FROM pos_order_line AS p, res_partner c, pos_order o WHERE (o.state!=\'draft\' and o.state!=\'cancel\' and o.partner_id is not NULL) and p.order_id = o.id and o.partner_id = c.id group by c.name, c.mobile, c.phone, c.email order by total DESC limit %s'
        cr.execute(query, (self.quantity,))
        partners = cr.dictfetchall()
        return partners

    def _get_objs_for_report(self, docids, data):
        if docids:
            ids = docids
        elif data and 'context' in data:
            ids = data["context"].get('active_ids', [])
        else:
            ids = self.env.context.get('active_ids', [])
        return self.env[self.env.context.get('active_model')].browse(ids)

    def excel_report(self):
        user_tz_dtm.get_timezone(self)
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'pos.order'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report',
                'report_name': 'report_pos_top20_customer.xlsx_top_customer',
                'context': dict(self.env.context, report_file='top_customer'),
                'data': datas,
                'report_type': 'xlsx'
                }

class TopCustomerXlsx(models.AbstractModel):
    _name = 'report.report_pos_top20_customer.xlsx_top_customer'
    _inherit = 'report.report_xlsx.abstract'

    def get_top20_customer(self, quantity):
        cr = self.env.cr
        states = ('cancel','draft')
        query = """
        SELECT rp.name, rp.phone, rp.mobile, rp.email, sum((pol.qty * pol.price_unit) * (100 - pol.discount) / 100) as total FROM pos_order_line AS pol 
        inner join pos_order as po on po.id = pol.order_id
        inner join res_partner rp on rp.id = po.partner_id
        WHERE po.state not in %s 
        group by rp.id 
        order by total DESC limit %d
        """ % (states,int(quantity))
        cr.execute(query)
        partners = cr.dictfetchall()
        return partners

    def generate_xlsx_report(self, workbook, data, lines):
        user_lang = user_tz_dtm.get_language(self)
        currency_num_format = f"#{user_lang.thousands_sep}##0{user_lang.decimal_point}{self.env.user.company_id.currency_id.decimal_places * '0'}"
        #print('currency_num_format=',currency_num_format)
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8_currency = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,'num_format':currency_num_format})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.write(0, 0, 'No.', format21)
        sheet.set_column(0,0,5)
        sheet.write(0, 1, 'Customer', format21)
        sheet.set_column(1, 1, 25)
        sheet.write(0, 2, 'Phone', format21)
        sheet.set_column(2, 2, 15)
        sheet.write(0, 3, 'Mobile', format21)
        sheet.set_column(3, 3, 15)
        sheet.write(0, 4, 'Email', format21)
        sheet.set_column(4, 4, 15)
        sheet.write(0, 5, 'Total', format21)
        sheet.set_column(5, 5, 15)
        partners = self.get_top20_customer(data['form']['quantity'])
        row = 0
        serial = 0
        for partner in partners:
            row = row + 1
            serial = serial + 1
            sheet.write(row, 0, int(serial), font_size_8)
            sheet.write(row, 1, partner['name'], font_size_8)
            sheet.write(row, 2, partner['phone'], font_size_8)
            sheet.write(row, 3, partner['mobile'], font_size_8)
            sheet.write(row, 4, partner['email'], font_size_8)
            sheet.write_number(row, 5, partner['total'], font_size_8_currency)
