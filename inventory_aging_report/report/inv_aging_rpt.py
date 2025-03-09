# -*- coding: utf-8 -*-
from odoo import models
from .. import user_tz_dtm
from odoo.tools.float_utils import float_is_zero
from datetime import datetime

class InvAgingReportXls(models.AbstractModel):
    _name = 'report.inv_aging_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Inventory Aging Report'

    
    def get_query_res(self,query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()   
    
    def generate_xlsx_report(self, workbook, datas, wiz_obj):
        obj_product = self.env['product.product']
        obj_stock_move = self.env['stock.move']
        product_uom_dp = self.env.ref('product.decimal_product_uom')
        rec = wiz_obj
        user_lang = user_tz_dtm.get_language(self)
        currency_num_format = f"#{user_lang.thousands_sep}##0{user_lang.decimal_point}{rec.currency_id.decimal_places * '0'}"
        uom_num_format = f"###0.{product_uom_dp.digits * '0'}"
        col_right = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'right','valign': 'vcenter'})
        col_right_currency = workbook.add_format(
            {'bold': True, 'font_size': 10, 'align': 'right', 'num_format': currency_num_format,
             'valign': 'vcenter'})
        #col_right_uom = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'right', 'num_format': uom_num_format})
        row_right_uom = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': uom_num_format})
        row_left = workbook.add_format({'font_size': 10, 'align': 'left'})
        #row_left_number = workbook.add_format({'font_size': 10,'align': 'left','num_format':currency_num_format})
        row_right = workbook.add_format({'font_size': 10, 'align': 'right'})
        #row_center = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter'})
        row_right_currency = workbook.add_format({'font_size': 10, 'align': 'right', 'num_format': currency_num_format})
        col_left = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'left', 'valign': 'vcenter'})
        col_center = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'})
        #col_center_main = workbook.add_format({'bold': True,'font_size': 10,'align': 'center','valign':'vcenter'})
        #col_total = workbook.add_format({'bold': True, 'font_size': 10,
        #                                 'align': 'right', 'valign': 'vcenter',
        #                                 'border':1,'bg_color':'#e6e6e6'})
        #col_number = workbook.add_format({'bold': True,'font_size': 10,'align': 'center','num_format':currency_num_format})
        sheet = workbook.add_worksheet("Stock Aging"[:31])

        #filters = rec.get_report_filters()
        row_count = 0
        filters = rec.get_report_filters()
        row_count += 1
        sheet.merge_range(row_count, 0, row_count, 23, self.env.user.company_id.name, col_left)
        row_count += 1
        sheet.merge_range(row_count, 0, row_count, 23,
                          f"INVENTORY AGING REPORT AS OF -> {user_tz_dtm.get_date_str(self, rec.date)}", col_left)
        row_count += 1
        for filt in filters:
            row_count += 1
            sheet.merge_range(row_count, 0, row_count, 1, filt.get('label', ''), col_left)
            sheet.merge_range(row_count, 2, row_count, 23, filt.get('value', ''), col_left)

        row_count += 2
        sheet.merge_range(row_count, 0, row_count + 1, 0, "Sl.No.", col_right)
        sheet.set_column(0, 0, 5)
        sheet.merge_range(row_count, 1, row_count + 1, 1, "Barcode", col_left)
        sheet.set_column(1, 1, 15)
        sheet.merge_range(row_count, 2, row_count + 1, 2, "Item Code", col_left)
        sheet.set_column(2, 2, 12)
        sheet.merge_range(row_count, 3, row_count + 1, 3, "Product Category", col_left)
        sheet.set_column(3, 3, 18)
        sheet.merge_range(row_count, 4, row_count + 1, 4, "Item Description", col_left)
        sheet.set_column(4, 4, 18)
        sheet.merge_range(row_count, 5, row_count + 1, 5, "Warehouse", col_left)
        sheet.set_column(5, 5, 15)
        sheet.merge_range(row_count, 6, row_count + 1, 6, "Cost Price", col_right)
        sheet.set_column(6, 6, 12)
        sheet.merge_range(row_count, 7, row_count + 1, 7, "Retail Selling Price", col_right)
        sheet.set_column(7, 7, 18)
        sheet.merge_range(row_count, 8, row_count + 1, 8, "Receipt Date", col_left)
        sheet.set_column(8, 8, 12)
        sheet.merge_range(row_count, 9, row_count + 1, 9, "Lot Number", col_left)
        sheet.set_column(9, 9, 15)
        sheet.merge_range(row_count, 10, row_count + 1, 10, "Expiry Date", col_left)
        sheet.set_column(10, 10, 18)
        sheet.merge_range(row_count, 11, row_count + 1, 11, "UOM", col_left)
        sheet.set_column(11, 11, 10)
        sheet.merge_range(row_count, 12, row_count + 1, 12, "Available Qty", col_right)
        sheet.set_column(12, 12, 18)
        sheet.merge_range(row_count, 13, row_count + 1, 13, "Stock Value", col_right)
        sheet.set_column(13, 13, 15)
        aging_cols = rec._get_aging_cols()
        col_count = 13
        sheet.merge_range(row_count, col_count + 1, row_count, col_count + 1 + 9, "Aging from the date of receipt", col_center)
        row_count += 1
        for col in aging_cols:
            col_count += 1
            sheet.write(row_count, col_count, col + " \nDays",col_center)
            sheet.set_row(row_count, 30)
            sheet.set_column(col_count,col_count,10)
        #print("_get_aging_dates=",rec._get_aging_dates())
        #print("_get_report_details=",rec._get_report_details())
        rpt_data = rec._get_print_data()
        #print('rpt_data=',rpt_data)
        sl_no = 0
        row_count += 0
        totals = {'stock_value':0}
        age = 1
        while age <= 10:
            totals["aging"+str(age)] = 0
            age += 1
        #move_ids_count = 0
        #obj_stock_val_adjstmnt_lines = self.env['stock.valuation.adjustment.lines']
        #obj_stock_val_layer = self.env['stock.valuation.layer']
        date_to = datetime.strptime(wiz_obj.date.strftime("%Y-%m-%d") + " 21:59:59","%Y-%m-%d %H:%M:%S")
        product_avg_cost = {}
        #print('rpt_data=',rpt_data)
        for po_sml in rpt_data:
            if 1==2 and \
            not po_sml.get('move_ids_purchase',[]) :
                continue
            #value = 0
            qty = 0
            #lot_id = po_sml['lot_id'] is not 0 and po_sml['lot_id'] or False
            for which in ['purchase', 'out', 'in']:
                if not po_sml.get('move_ids_'+which, []):
                    continue
                #moves_to_do = obj_stock_move.browse(po_sml.get('move_ids_'+which, []))
                sign = which in ['purchase', 'in'] and 1 or -1
                product = obj_product.browse(po_sml['product_id'])
                #
                if product.id not in product_avg_cost:
                    average_cost = product.with_company(self.env.company).standard_price
                    if product.cost_method == 'fifo':
                        quantity = product.with_company(self.env.company).with_context(to_date=date_to).quantity_svl
                        if float_is_zero(quantity, precision_rounding=product.uom_id.rounding):
                            continue
                        average_cost = product.with_company(self.env.company).with_context(to_date=date_to).value_svl / quantity
                    product_avg_cost[product.id] = average_cost
                average_cost = product_avg_cost.get(product.id)
                #
                qty += sign * po_sml['qty_' + which]
                if 1 == 2:
                    for move in moves_to_do:
                        if 1==1:
                            continue
                        #move_ids_count += 1
                        move_total_cost = sum(move.account_move_ids.mapped('amount_total_signed'))
                        landed_cost = 0
                        #print('move_total_cost=', move_total_cost, move, sign, which)
                        landed_costs = obj_stock_val_adjstmnt_lines.search([('move_id','=',move.id),
                                                                           ('cost_id.state','=','done')]).mapped('cost_id')
                        #print('landed_costs=',landed_costs,move)
                        for lc in landed_costs:
                            val_layer = obj_stock_val_layer.search([('product_id','=',move.product_id.id),
                                                                    ('stock_landed_cost_id','=',lc.id)])
                            landed_cost += sum(val_layer.mapped('value'))
                        #print('landed_cost=',landed_cost)
                        move_total_cost += landed_cost
                        if not move_total_cost:
                            continue
                        standard_price = product.standard_price
                        if not move_total_cost: #(probably internal transfer)
                            standard_price = sum(obj_stock_move.browse(po_sml['move_ids_purchase']).mapped('price_unit')) / len(po_sml['move_ids_purchase'])
                            move_total_cost = standard_price * sum(move.move_line_ids.mapped('qty_done'))
                        #if multiple line+diff lot in move
                        if len(move.move_line_ids.ids) > 1 and len(list(set(move.move_line_ids.mapped('lot_id')))) > 1:
                            move_total_qty = sum(move.move_line_ids.mapped('qty_done'))
                            unit_cost = move_total_qty and (move_total_cost / move_total_qty) or standard_price
                            #po_sml['qty_'+which] = sum(move.move_line_ids.filtered(lambda l: l.lot_id.id == lot_id).mapped('qty_done'))
                            value += sign * (unit_cost * po_sml['qty_'+which])
                            #qty += sign * po_sml['qty_'+which]
                        else:
                            value += sign * move_total_cost
                            #print('sign=',move,sign)
                            #Fprint('move_total_cost=',move_total_cost)
                            #qty += sign * po_sml['qty_'+which]
            if not qty:
                continue
            to_update = {'cost_price': average_cost,#value / qty,
                         'retail_price': product.lst_price,
                         'qty_available': qty,
                         'stock_value': qty * average_cost#value
                         }
            po_sml.update(to_update)
            row_count += 1
            sl_no += 1
            #print("printtt")
            sheet.write_number(row_count, 0, sl_no, row_right)
            sheet.write(row_count, 1, po_sml.get('barcode',''), row_left)
            sheet.write(row_count, 2, po_sml.get('default_code',''), row_left)
            sheet.write(row_count, 3, po_sml.get('product_category', ''), row_left)
            sheet.write(row_count, 4, po_sml.get('product_name', ''), row_left)
            sheet.write(row_count, 5, po_sml.get('warehouse', ''), row_left)
            sheet.write_number(row_count, 6, po_sml.get('cost_price', ''), row_right_currency)
            sheet.write_number(row_count, 7, po_sml.get('retail_price', ''), row_right_currency)
            sheet.write(row_count, 8, po_sml.get('date_receipt', False) and user_tz_dtm.get_date_str(self,po_sml['date_receipt']) or '', row_left)
            sheet.write(row_count, 9, po_sml.get('lot_name', ''), row_left)
            sheet.write(row_count, 10, po_sml.get('lot_expiry', None) is not None and user_tz_dtm.get_date_str(self,po_sml['lot_expiry']) or '', row_left)
            sheet.write(row_count, 11, po_sml.get('uom', ''), row_left)
            qty_avail = po_sml.get('qty_available', 0)
            sheet.write_number(row_count, 12, qty_avail, int(qty_avail) == qty_avail and row_right or row_right_uom)
            sheet.write_number(row_count, 13, po_sml.get('stock_value', 0), row_right_currency)
            sheet.write_number(row_count, 13 + po_sml['aging_col'], po_sml.get('stock_value', 0), row_right_currency)
            totals['aging'+str(po_sml['aging_col'])] += po_sml.get('stock_value', 0)
            totals['stock_value'] += po_sml.get('stock_value', 0)
        #totals
        #print('move_ids_count=',move_ids_count)
        if totals['stock_value'] > 0:
            row_count += 1
            col_count = 13
            sheet.write_number(row_count, col_count, totals.get('stock_value', 0), col_right_currency)
            age = 1
            while age <= 10:
                col_count += 1
                sheet.write_number(row_count, col_count, totals.get("aging"+str(age),0), col_right_currency)
                age += 1
        workbook.close()
