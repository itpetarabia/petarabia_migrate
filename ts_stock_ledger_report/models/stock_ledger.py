import logging
from pprint import pprint
from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockLedgerReport(models.TransientModel):
    _name = 'ts.stock.ledger.report'

    date_to = fields.Date('Date to', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
        # self.warehouse_ids = 

    # Generate xlsx report
    def action_generate_xlsx_report(self):
        if not self.warehouse_ids.ids:
            self.warehouse_ids = [r.id for r in self.env['stock.warehouse'].search([('active', '=', True)])]
        data = {
            'warehouse_ids':self.warehouse_ids.ids,
            'date_to': self.date_to,
            }
        return self.env.ref('ts_stock_ledger_report.action_stock_ledger_xlsx_report').report_action(self, data=data)

    # def action_fill_all_warehouses(self):


class StockLedgerXlsxReport(models.AbstractModel):
    _name = 'report.ts_stock_ledger_report.stock_ledger_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    
    def _assign_location_to_warehouse(self, wh_collection, wh_id, loc_id):
        wh_locations = wh_collection.get(wh_id, [].copy())
        wh_locations.append(loc_id)
        wh_collection[wh_id] = wh_locations
        

    def _vet_warehouse_locations(self, warehouse_ids):
        vetted_whs = []
        vetted_wh_ids = []

        warehouses = self.env['stock.warehouse'].browse(warehouse_ids)
        for wh, id in zip(warehouses, warehouse_ids):
            if wh.lot_stock_id.usage != 'internal':
                _logger.error('The warehouse {wh.name} is not linked to an internal location, so it will be excluded.')
            else:
                vetted_whs.append(wh)
                vetted_wh_ids.append(id)
        return vetted_whs, vetted_wh_ids

        
        
    def _get_product_name(self, prod):
        variant = prod.product_template_attribute_value_ids._get_combination_name()
        name = variant and "%s (%s)" % (prod.name, variant) or prod.name
        return name

    def generate_xlsx_report(self, workbook, data, partners):
        try:
            sheet = workbook.add_worksheet('Stock Warehouse Report')
            title1 = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11, 'bg_color': '#00ab41', 'border': True, 'text_wrap': True})
            title3 = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11, 'bg_color': '#fff2cd', 'border': True})
            header_row_style = workbook.add_format({'bold': True, 'align': 'center', 'border': True})
            header_row_style1 = workbook.add_format({'bold': True, 'align': 'center', 'border': True, 'bg_color': '#D9E1F2'})
            digit_style = workbook.add_format({'align': 'center', 'bg_color': '#dae1f1', 'border': True})

            sheet.set_column('E:E',30)
            sheet.set_column('F:F',40)
            sheet.set_column('G:G',40)


            # Warehouse and Locations
            warehouse_ids =  data.get('warehouse_ids')
            warehouses, warehouse_ids = self._vet_warehouse_locations(warehouse_ids)

            all_locations = self.env['stock.location'].search([
                ('active', '=', True),
                ('usage', '=', 'internal'),
                ])
            locations = []
            warehouse_id_to_location_ids = {}
            for loc in all_locations: 
                wh_id = loc.get_warehouse().id
                if wh_id in warehouse_ids:
                    self._assign_location_to_warehouse(warehouse_id_to_location_ids, wh_id, loc.id)
                    locations.append(loc)
            location_ids = [l.id for l in locations]



            # Header row
            MAIN_HEADER_ROW=1
            WAREHOUSE_START_COLUMN = 4
            for index, wh in enumerate(warehouses):
                sheet.write(MAIN_HEADER_ROW, WAREHOUSE_START_COLUMN+index, wh.name, title1)

            date_to = data.get('date_to', False)
            sheet.merge_range(MAIN_HEADER_ROW, 0, MAIN_HEADER_ROW, 3,
                              "Report Till:"+ str(date_to) ,title3)

            sheet.set_column(0, 0, 15)
            sheet.set_column(1, 1, 35)
            sheet.set_column(2, 2, 10)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 11, 20)
            sheet.freeze_panes(2, 0)

            SUBHEADER_ROW = 2
            col = 0
            sheet.write(SUBHEADER_ROW, col, 'Barcode', header_row_style1)
            sheet.write(SUBHEADER_ROW, col+1, 'Product', header_row_style1)
            sheet.write(SUBHEADER_ROW, col+2, 'Price', header_row_style1)
            sheet.write(SUBHEADER_ROW, col+3, 'Lot/Serial no', header_row_style1)


            date_to = data.get('date_to', False)
            date_to = datetime.strptime(date_to, DF)

            date_to = data.get('date_to', False)
            domain = [
                ('in_date', '<=', date_to),
                ('location_id', 'in', location_ids),
                ]
            stock_quants = self.env['stock.quant'].search(domain, order="in_date")
            stock_quants = stock_quants.filtered(lambda mv: mv.quantity != 0)

            # Form Products
            product_list = list(set([
                (q.product_id.id,
                 q.lot_id.id,
                 q.lot_id.name or '',
                 q.product_id.name and self._get_product_name(q.product_id) or '',
                 q.product_id.list_price,
                 q.product_id.barcode or '')
                for q in stock_quants
                ]))
            product_list = sorted(product_list, key=lambda x: (x[-1], x[3]))


            row = SUBHEADER_ROW + 1
            for prod_id, lot_id, lot_name, prod_name, prod_price, prod_barcode in product_list:
                sheet.write(row, col, prod_barcode)
                sheet.write(row, col+1, prod_name)
                sheet.write(row, col+2, prod_price)
                sheet.write(row, col+3, lot_name)
                for wh_column, wh in enumerate(warehouses):
                    loc_ids_in_warehouse = warehouse_id_to_location_ids[wh.id]
                    quants_in_warehouse = stock_quants.search([
                        ('location_id', 'in', loc_ids_in_warehouse),
                        ('product_id', '=', prod_id),
                        ('lot_id', '=', lot_id),
                        ])
                    total_of_quants = sum([q.quantity for q in quants_in_warehouse])
                    sheet.write(row, col + 4+wh_column, total_of_quants, digit_style)
                row += 1
        except Exception as e:
            _logger.error(e)
            raise e