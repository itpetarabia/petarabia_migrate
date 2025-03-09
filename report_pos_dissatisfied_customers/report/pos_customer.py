0# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from datetime import datetime ,date
from dateutil.relativedelta import relativedelta

class PosDissatisfiedCustomers(models.TransientModel):
    _name = 'pos.dissatisfied.customer.wizard'
    _description = 'Point of Sale Dissatisfied customer Report'

    user_id = fields.Many2one('res.users', string='User', index=True, tracking=True, track_sequence=2, default=lambda self: self.env.user)
    duration = fields.Integer(string="Duration(Days)", required=True, default=90)
    customer_limit = fields.Integer("Customer Limit",default=1000,required=True)

    def generate_report(self):
        data = {}
        return self.env.ref('report_pos_dissatisfied_customers.pos_dissatisfied_customer_report').report_action([], data=data)

    def excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'pos.dissatisfied.customer.wizard'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('report_pos_dissatisfied_customers.dissatisfiedcustomer_xlsx').report_action(self, data=datas)


    def get_dissatisfied_customer(self):
        dates = date.today() - relativedelta(days=self.duration)
        cr = self.env.cr
        query = \
            """
            SELECT rp.name,
            rp.mobile, 
            rp.phone, rp.email, 
            (select date_order from pos_order as po where po.partner_id = rp.id and po.state not in ('draft','cancel') order by date_order DESC limit 1) as last_date 
            FROM res_partner as rp
            where (select date_order from pos_order as po where po.partner_id = rp.id and po.state not in ('draft','cancel') order by po.date_order DESC limit 1) <= '%s' order by last_date DESC limit %d
            """ % (dates,self.customer_limit > 0 and self.customer_limit or 1000)
        cr.execute(query)
        partners = cr.dictfetchall()
        return partners

class PosDissatisfiedCustomersXlsx(models.AbstractModel):

    _name = 'report.report_pos_dissatisfied_customers.xlsx_pos_dissatisfied'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        #format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
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
        sheet.write(0, 1, 'Customer', format21)
        sheet.write(0, 2, 'Mobile', format21)
        sheet.write(0, 3, 'Phone', format21)
        sheet.write(0, 4, 'Email', format21)
        sheet.write(0, 5, 'Last Visit', format21)
        sheet.write(0, 6, 'Days', format21)
        partners = lines.get_dissatisfied_customer()
        row = 0
        serial = 0
        for partner in partners:
            row = row + 1
            serial = serial + 1
            sheet.write(row, 0, serial, font_size_8)
            sheet.write(row, 1, partner['name'], font_size_8)
            sheet.write(row, 2, partner['mobile'], font_size_8)
            sheet.write(row, 3, partner['phone'], font_size_8)
            sheet.write(row, 4, partner['email'], font_size_8)
            sheet.write(row, 5, partner['last_date'].strftime("%d-%b-%Y"), font_size_8)
            sheet.write(row, 6, (datetime.now() - partner['last_date']).days, font_size_8)

class PosSlowCustomers(models.TransientModel):
    _name = 'pos.slow.customer.wizard'
    _description = 'Point of Sale Slow customer Report'

    def generate_report(self):
        data = {}
        return self.env.ref('report_pos_dissatisfied_customers.pos_slow_customer_report').report_action([], data=data)

    def excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'pos.slow.customer.wizard'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('report_pos_dissatisfied_customers.slowcustomer_xlsx').report_action(self, data=datas)

    def get_slow_customer(self):
        customers = {}
        month1 = date.today() - relativedelta(months=4)
        month2 = date.today() - relativedelta(months=3)
        month3 = date.today() - relativedelta(months=2)
        month4 = date.today() - relativedelta(months=1)
        orders1 = self.env['pos.order'].read_group([('state', 'not in', ('draft','cancel')), ('partner_id', '!=', False), ('date_order', '>=', month1), ('date_order', '<=', month2)], ['partner_id'], groupby='partner_id')
        partners1 = [data['partner_id'][0] for data in orders1]
        orders2 = self.env['pos.order'].read_group([('state', 'not in', ('draft','cancel')), ('partner_id', 'in', partners1), ('date_order', '>=', month2), ('date_order', '<=', month3)], ['partner_id'], groupby='partner_id')
        partners2 = [data['partner_id'][0] for data in orders2]
        orders3 = self.env['pos.order'].read_group([('state', 'not in', ('draft','cancel')), ('partner_id', 'in', partners2), ('date_order', '>=', month3), ('date_order', '<=', month4)], ['partner_id'], groupby='partner_id')
        partners = [data['partner_id'][0] for data in orders3]
        i = 0
        for partner in partners:
            order = self.env['pos.order'].search([('state', 'not in', ('draft','cancel')), ('partner_id', '=', partner), ('date_order', '>=', month4)], limit=1)
            if not order:
                p = self.env['res.partner'].browse(partner)
                orders = self.env['pos.order'].search([('state', 'not in', ('draft','cancel')), ('partner_id', '=', partner)], order='date_order DESC')
                branch = orders[0].session_id.config_id.name
                total = 0
                for o in orders:
                    total += o.amount_total - o.amount_tax
                customers[i]= {'name': p.name, 'email': p.email, 'mobile': p.mobile, 'phone': p.phone, 'total': total, 'branch': branch}
                i = i+1
                
        return customers

class PosDissatisfiedCustomersXlsx(models.AbstractModel):

    _name = 'report.report_pos_dissatisfied_customers.xlsx_pos_slow_customer'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        #format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
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
        sheet.write(0, 1, 'Customer', format21)
        sheet.write(0, 2, 'Mobile', format21)
        sheet.write(0, 3, 'Phone', format21)
        sheet.write(0, 4, 'Email', format21)
        sheet.write(0, 5, 'Last Branch', format21)
        sheet.write(0, 6, 'Total Purchased', format21)
        partners = lines.get_slow_customer()
        row = 0
        serial = 0
        for i in range(0, len(partners)):
            row = row + 1
            serial = serial + 1
            sheet.write(row, 0, serial, font_size_8)
            sheet.write(row, 1, partners[i]['name'], font_size_8)
            sheet.write(row, 2, partners[i]['mobile'], font_size_8)
            sheet.write(row, 3, partners[i]['phone'], font_size_8)
            sheet.write(row, 4, partners[i]['email'], font_size_8)
            sheet.write(row, 5, partners[i]['branch'], font_size_8)
            sheet.write(row, 6, partners[i]['total'], font_size_8)
