from odoo import models, fields
from datetime import datetime, timedelta
from .. import user_tz_dtm
from odoo.exceptions import UserError

class InvBillReportWiz(models.TransientModel):
    _name = 'inv.aging.rpt.wiz'
    _description = 'Inventory Aging Report Wizard'

    def get_query_res(self,query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall() or []
    
    def _get_is_module_installed(self, module_name):
        qry = f"select state from ir_module_module where name='{module_name}' and state ='installed'"
        qry_res = self.get_query_res(qry)  
        if qry_res:
            return True
        return False

    def get_record(self, model_name, domain=[]):
        return self.env[model_name].search(domain)
    
    def get_record_obj(self, model_name, ids):
        return self.env[model_name].browse(ids)
        
    def validate_report(self):
        user_tz_dtm.get_timezone(self)
        msg = []
        if msg:
            raise UserError("\n\n".join(msg))
    
    def generate_report(self):
        self.validate_report()
        return self.sudo().export_xls()

    def _get_print_data(self):
        return self._get_product_info()

    def get_in_or_equal(self, ids=[]):
        if len(ids) > 1:
            return f"in {tuple(ids)}"
        return f"= {ids[0]}"

    def _get_product_info(self):
        company_ids = self._context.get('allowed_company_ids', []) or self.env.user.company_id.ids
        #obj_stock_loc = self.env['stock.location']
        aging_dates = self._get_aging_dates()
        #print('_get_aging_dates=', aging_dates)
        #get all purchase - grouped by warehouse,receipt date,product,lot
        if 1==2:
            where_clause = f"sml.company_id {self.get_in_or_equal(company_ids)} AND sp.date_done::Date <= '{self.date}' AND sml.state = 'done' AND sp.state = 'done'"
            where_clause += " AND pp.active = true"
            where_clause += self.prod_categ_ids and f" AND pt.categ_id {self.get_in_or_equal(self.prod_categ_ids.ids)}" or ""
            where_clause += self.warehouse_ids and f" AND sl_dest.mt_warehouse_id {self.get_in_or_equal(self.warehouse_ids.ids)}" or ""
            where_clause += " AND sml.product_id=21787"
            qry = """
            select 
            sw.id as warehouse_id, max(sp.date_done::Date) as date_receipt, pp.id AS product_id, 
            COALESCE(spl.id,0) AS lot_id,
            COALESCE(spl.name,'') as lot_name, spl.expiration_date::Date as lot_expiry,
            sum (sml.qty_done) as qty_purchase,uu.name as uom,
            pt.name as product_name,COALESCE(pp.barcode,'') AS barcode, 
            COALESCE(pp.default_code,'') as default_code,pc.complete_name as product_category,
            sw.name as warehouse,
            array_agg(distinct sm.id) as move_ids_purchase
            FROM stock_move_line as sml
            inner join stock_location as sl_source on sl_source.id = sml.location_id AND sl_source.usage = 'supplier'
            inner join stock_location as sl_dest on sl_dest.id = sml.location_dest_id AND sl_dest.usage = 'internal'
            inner join product_product as pp on pp.id = sml.product_id
            inner join product_template as pt on pt.id = pp.product_tmpl_id
            inner join product_category as pc on pc.id = pt.categ_id
            inner join uom_uom as uu on uu.id = pt.uom_id
            inner join stock_move as sm on sm.id = sml.move_id
            inner join stock_picking as sp on sp.id = sm.picking_id
            inner join stock_warehouse as sw on sw.id = sl_dest.mt_warehouse_id
            left join stock_production_lot AS spl ON spl.id = sml.lot_id
            where %s
            group by sw.id, pp.id, spl.id, pt.id, pc.id, uu.id
            """ % (where_clause)
        if 1==1:
            where_clause = f"sml.company_id {self.get_in_or_equal(company_ids)} AND sm.date::Date <= '{self.date}' AND sml.state = 'done'"
            where_clause += " AND pp.active = true"
            where_clause += self.prod_categ_ids and f" AND pt.categ_id {self.get_in_or_equal(self.prod_categ_ids.ids)}" or ""
            where_clause += self.warehouse_ids and f" AND sl_dest.mt_warehouse_id {self.get_in_or_equal(self.warehouse_ids.ids)}" or ""
            where_clause += self.product_ids and f" AND sml.product_id {self.get_in_or_equal(self.product_ids.ids)}" or ""
            qry = """
            select 
            sw.id as warehouse_id, max(sm.date::Date) as date_receipt, pp.id AS product_id, 
            COALESCE(spl.id,0) AS lot_id,
            COALESCE(spl.name,'') as lot_name, spl.expiration_date::Date as lot_expiry,
            sum (sml.qty_done) as qty_purchase,uu.name as uom,
            pt.name as product_name,COALESCE(pp.barcode,'') AS barcode, 
            COALESCE(pp.default_code,'') as default_code,pc.complete_name as product_category,
            sw.name as warehouse,
            array_agg(distinct sm.id) as move_ids_purchase
            FROM stock_move_line as sml
            inner join stock_location as sl_source on sl_source.id = sml.location_id
            inner join stock_location as sl_dest on sl_dest.id = sml.location_dest_id AND sl_dest.usage = 'internal'
            inner join product_product as pp on pp.id = sml.product_id
            inner join product_template as pt on pt.id = pp.product_tmpl_id
            inner join product_category as pc on pc.id = pt.categ_id
            inner join uom_uom as uu on uu.id = pt.uom_id
            inner join stock_move as sm on sm.id = sml.move_id
            inner join stock_warehouse as sw on sw.id = sl_dest.mt_warehouse_id
            left join stock_production_lot AS spl ON spl.id = sml.lot_id
            where %s
            group by sw.id, pp.id, spl.id, pt.id, pc.id, uu.id
            """ % (where_clause)
        qry_res_purchase = self.get_query_res(qry)
        #print('qry_res_purchase=',qry_res_purchase)
        #all out - (purchase return,sale, inventory adjustment,inter transfer from ,, ie from warehouse == internal locations)
        where_clause = f"sml.company_id {self.get_in_or_equal(company_ids)} AND sml.date::Date <= '{self.date}' AND sml.state = 'done'"
        where_clause += " AND pp.active = true"
        where_clause += self.prod_categ_ids and f" AND pt.categ_id {self.get_in_or_equal(self.prod_categ_ids.ids)}" or ""
        where_clause += self.warehouse_ids and f" AND sl_source.mt_warehouse_id {self.get_in_or_equal(self.warehouse_ids.ids)}" or ""
        where_clause += self.product_ids and f" AND sml.product_id {self.get_in_or_equal(self.product_ids.ids)}" or ""
        all_out_det = {}
        qry = """
            select
            sum (sml.qty_done) as qty_out, 
            array_agg(distinct sm.id) as move_ids_out,
            sw.id as warehouse_id, sml.product_id, COALESCE(sml.lot_id,0) as lot_id
            from stock_move_line as sml
            inner join product_product as pp on pp.id = sml.product_id
            inner join product_template as pt on pt.id = pp.product_tmpl_id
            inner join stock_location as sl_source on sl_source.id = sml.location_id AND sl_source.usage = 'internal'
            inner join stock_location as sl_dest on sl_dest.id = sml.location_dest_id AND sl_dest.id != sl_source.id
            inner join stock_move as sm on sm.id = sml.move_id
            inner join stock_warehouse as sw on sw.id = sl_source.mt_warehouse_id
            where %s 
            group by sw.id, sml.product_id, sml.lot_id
            """ % (where_clause)
        qry_res_all_out = self.get_query_res(qry)
        #print('qry_res_all_out=', qry_res_all_out)
        for r in qry_res_all_out:
            all_out_det.setdefault(r['warehouse_id'], {})
            all_out_det[r['warehouse_id']].setdefault(r['product_id'], {})
            vals = {}
            for k in ['qty_out', 'move_ids_out']:
                vals[k] = r[k]
            all_out_det[r['warehouse_id']][r['product_id']][r['lot_id']] = vals
        if 1==2:
            #print('all_out_det=',all_out_det)
            # all in - except purchase (sale return, inventory adjustment,inter transfer to ,, ie to warehouse == internal locations)
            where_clause = f"sml.company_id {self.get_in_or_equal(company_ids)} AND sml.date::Date <= '{self.date}' AND sml.state = 'done'"
            where_clause += " AND pp.active = true"
            where_clause += self.prod_categ_ids and f" AND pt.categ_id {self.get_in_or_equal(self.prod_categ_ids.ids)}" or ""
            where_clause += self.warehouse_ids and f" AND sl_dest.mt_warehouse_id {self.get_in_or_equal(self.warehouse_ids.ids)}" or ""
            where_clause += " AND sml.product_id=21787"
            all_in_det = {}
            qry = """
                    select
                    sum (sml.qty_done) as qty_in, 
                    array_agg(distinct sm.id) as move_ids_in,
                    sw.id as warehouse_id, sml.product_id, COALESCE(sml.lot_id,0) as lot_id
                    from stock_move_line as sml
                    inner join product_product as pp on pp.id = sml.product_id
                    inner join product_template as pt on pt.id = pp.product_tmpl_id
                    inner join stock_location as sl_source on sl_source.id = sml.location_id AND sl_source.usage != 'supplier'
                    inner join stock_location as sl_dest on sl_dest.id = sml.location_dest_id AND sl_dest.id != sl_source.id
                        AND sl_dest.usage = 'internal'
                    inner join stock_move as sm on sm.id = sml.move_id
                    inner join stock_warehouse AS sw ON sw.id = sl_dest.mt_warehouse_id
                    where %s 
                    group by sw.id, sml.product_id, sml.lot_id
                    """ % (where_clause)
            qry_res_all_in = self.get_query_res(qry)
            #print('qry_res_all_in=', qry_res_all_in)
            for r in qry_res_all_in:
                all_in_det.setdefault(r['warehouse_id'], {})
                all_in_det[r['warehouse_id']].setdefault(r['product_id'], {})
                vals = {}
                for k in ['qty_in', 'move_ids_in']:
                    vals[k] = r[k]
                all_in_det[r['warehouse_id']][r['product_id']][r['lot_id']] = vals

        #update purhcase dict
        for r in qry_res_purchase:
            r['aging_col'] = 10
            age_col_count = 0
            for dts in aging_dates:
                age_col_count += 1
                if r['date_receipt'] >= dts[0] and r['date_receipt'] <= dts[1]:
                    r['aging_col'] = age_col_count
                    break

            if all_out_det.get(r['warehouse_id'], {}).get(r['product_id'], {}).get(r['lot_id'],{}):
                r.update(all_out_det.get(r['warehouse_id'], {}).get(r['product_id'], {}).get(r['lot_id'],{}))
            if 1==2 and all_in_det.get(r['warehouse_id'], {}).get(r['product_id'], {}).get(r['lot_id'],{}):
                r.update(all_in_det.get(r['warehouse_id'], {}).get(r['product_id'], {}).get(r['lot_id'],{}))
        #has in but no purchase found in warehouse (to do)
        #print('qry_res_purchase=',qry_res_purchase)
        return qry_res_purchase

    def _get_aging_dates(self):
        date_to = self.date
        dates = []
        i = 0
        while i <= 7:
            i += 1
            dates.append([date_to - timedelta(days=self.period_length), date_to])
            date_to = date_to - timedelta(days=self.period_length)

        dates.append([date_to - timedelta(days=90), date_to])
        date_to = date_to - timedelta(days=90)
        dates.append([date_to - timedelta(days=95), date_to])
        #date_to = date_to - timedelta(days=95)
        return dates

    def _get_aging_cols(self):
        period_length = self.period_length
        starting_period = 0
        cols = []
        i = 0
        while i <= 6:
            i += 1
            cols.append(f"{str(starting_period != 0 and starting_period + 1 or starting_period)} - {str(starting_period + period_length)}")
            starting_period += period_length
        cols.append(f"181 - 270")
        cols.append(f"271 - 365")
        cols.append(f"Above 365")
        return cols

    date = fields.Date(required=True)
    prod_categ_ids = fields.Many2many('product.category','inv_aging_rpt_wiz_prod_categ_rel','wiz_id','categ_id',string='Product Categories')
    warehouse_ids = fields.Many2many('stock.warehouse','inv_aging_rpt_wiz_warehouse_rel','wiz_id','warehouse_id',string='Warehouses')
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.user.company_id.currency_id.id,
                                  string="Currency", required=True)
    company_id = fields.Many2one('res.company', 'Company', invisible=True, required=True,
                                 default=lambda self: self.env.user.company_id.id, copy=False, ondelete='cascade')
    user_id = fields.Many2one('res.users', 'Responsible', invisible=True, default=lambda self: self.env.user.id,
                              copy=False, required=True, ondelete='cascade')
    period_length = fields.Integer(default=30)
    product_ids = fields.Many2many('product.product','inv_aging_rpt_wiz_product_rel','wizard_id','product_id')

    def export_xls(self):
        user_tz_dtm.get_timezone(self)
        datas = {'ids': self._context.get('active_ids', []),
                 'model': self._name,
                 'form': self.read()[0]
                 }
        self = self.with_context(discard_logo_check=True)
        report_xml_id = self.env.ref('inventory_aging_report.report_xlsx_inv_aging')
        report_xml_id.report_file = f"Inventory Aging Report - {user_tz_dtm.get_date_str(self,self.date)}"
        return report_xml_id.report_action(self, data=datas)

    def get_report_filters(self):
        filters = []
        now_str = user_tz_dtm.get_tz_date_time_str(self,datetime.now())
        filters.append({'label':'Printed By','value': f"{self.env.user.display_name} - {now_str}"})
        self.prod_categ_ids and filters.append({'label':'Product Categories','value':", ".join(self.prod_categ_ids.mapped('display_name'))})
        self.warehouse_ids and filters.append({'label': 'Warehouses', 'value': ", ".join(self.warehouse_ids.mapped('display_name'))})
        return filters