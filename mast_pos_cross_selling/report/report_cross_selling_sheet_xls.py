from odoo import models, fields, api, _
#from odoo.exceptions import UserError
#from datetime import date
#from decimal import *
import pytz
import datetime
from . import user_tz_dtm

class ReportCrossSellingXlsx(models.AbstractModel):
    _name = 'report.mast_pos_cross_selling.report_cross_selling_sheet_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Cross Selling Report'

    def generate_xlsx_report(self, workbook, data, lines):
        merge_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#d3d3d3'})
        content_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'})
        content_format1 = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'})
        format3 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})

        data = lines.get_report_values_cross_selling()
        #print("dataaaaa==",data)
        sheet = workbook.add_worksheet('Cross Selling Report')
        sheet.merge_range('C2:D2', 'Cross Selling Report', header_format)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)


        user = self.env['res.users'].browse(self.env.uid)
        if user.tz:
            tz = pytz.timezone(user.tz)
            time = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        else:
            time = datetime.datetime.now()

        sheet.merge_range('B3:E3', 'Report Date: ' + str(time.strftime("%d-%m-%Y %H:%M %p")), format3)
        sheet.merge_range('B4:E4', 'Printed By: ' + str(user.name), format3)

        #sheet.merge_range('A3:C3', 'Today Date:' + ' ' ,  merge_format)
        sheet.merge_range('B5:E5', 'From:' + ' ' + user_tz_dtm.get_tz_date_time_str(self,lines.start_date) + '    ' + 'To:' + ' ' + user_tz_dtm.get_tz_date_time_str(self, lines.end_date), format3)
        # sheet.merge_range('A6:A7', '#', content_format)
        # sheet.merge_range('B6:C7', '#', content_format)

        sheet.write(7, 0, '#', header_format)
        sheet.write(7, 1, 'Salesman', header_format)
        sheet.write(7, 2, 'Point Of Sale', header_format)
        sheet.write(7, 3, 'Order Reference', header_format)
        sheet.write(7, 4, 'Total Quantity', header_format)
        sheet.write(7, 5, 'Total Amount', header_format)


        ref_no = 0
        row = 8
        total_quantity = 0.0
        total_amount = 0.0
        for record in data:
            print("record========",record)
            ref_no = ref_no + 1
            sheet.write(row, 0, ref_no, content_format)
            salesman = record['user_name']
            if record['po_id']:
                po_id = self.env['pos.order'].sudo().browse(record['po_id'])
                installed_modules = self.env['ir.module.module'].sudo().search([
                    ('name', '=', 'pos_hr'),
                    ('state', '=', 'installed'),
                ])
                if installed_modules and po_id.employee_id:
                    salesman = po_id.employee_id.name
            sheet.write(row, 1, salesman, content_format)
            sheet.write(row, 2, record['config'], content_format)
            sheet.write(row, 3, record['reference'], content_format)
            sheet.write(row, 4, record["quantity"], content_format)
            sheet.write(row, 5, round(record['amount'],3), content_format)
            total_quantity += record["quantity"]
            total_amount += record['amount']
            row += 1
        sheet.merge_range(row, 0, row, 3, 'Total', header_format)
        sheet.write(row, 4, total_quantity, header_format)
        sheet.write(row, 5, round(total_amount,3), header_format)