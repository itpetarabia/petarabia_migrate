import os
import aiohttp
import asyncio
import logging
from pprint import pformat
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.instashop.models.core import InstaConnector, ExtBarcodeList

_logger = logging.getLogger(__name__)

def log(text):
    _logger.info(pformat(text))
    # _logger.info(text)

class InstashopBasicConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    
    url = fields.Char(string='URL',config_parameter='instashop.url')
    # instashop_user = fields.Char(string="Username",config_parameter='instashop.user')
    # instashop_password = fields.Char(string="Password",config_parameter='instashop.password')
    api_key = fields.Char(string="API Key",config_parameter='instashop.api_key')
    instashop_products_batch_limit = fields.Char(string="Products Batch Limit",config_parameter='instashop.productsbatchlimit')
    
    def get_values(self):
        res = super().get_values()
        res.update(
            url=self.env['ir.config_parameter'].sudo().get_param('instashop.url'),
            # instashop_password=self.env['ir.config_parameter'].sudo().get_param('instashop.password'),
            # instashop_user=self.env['ir.config_parameter'].sudo().get_param('instashop.user'),
            api_key=self.env['ir.config_parameter'].sudo().get_param('instashop.api_key'),
            instashop_products_batch_limit=self.env['ir.config_parameter'].sudo().get_param('instashop.productsbatchlimit'),
        )
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('instashop.url', self.url)
        self.env['ir.config_parameter'].sudo().set_param('instashop.api_key', self.api_key)
        self.env['ir.config_parameter'].sudo().set_param('instashop.productsbatchlimit', self.instashop_products_batch_limit)
        
class InstashopConfig(models.Model):
    _name = 'pos.config.instashop'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'config_id'
    _description = 'Instashop Sync'
    
    config_id = fields.Many2one('pos.config', string='Point of Sale', required=True, tracking=True)
    instashop_id = fields.Char(string='Instashop ID', required=True, tracking=True)

    _sql_constraints = [('unique_pos', 'unique(config_id)', 'This POS has already been set.')]

    @api.model
    def _read_sql_fromfile(self, filename):
        directory_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'r') as file:
            text = file.read()
        text = text.replace(';', '')
        return text


    @api.model
    async def publish_to_instashop(self, instashop_data):
        url = self.env['ir.config_parameter'].sudo().get_param('instashop.url')
        api_key = self.env['ir.config_parameter'].sudo().get_param('instashop.api_key')
        conn = InstaConnector(api_key, url)

        # limit = 50
        # tasks = []
        async with aiohttp.ClientSession() as session:
            responses = []
            for instashop_id, prods in instashop_data.items():
                # tasks.append(asyncio.ensure_future(conn.update_products_faster(session, instashop_id, prods)))
                try:
                    res = conn.update_products_faster(session, instashop_id, prods)
                    responses.append(await res)
                    log(f'Instashop ID {instashop_id} Synced')
                except Exception as e:
                    _logger.error(e) # continue with next request too
                    log(f'Instashop ID {instashop_id} Failed Sync')
            # responses = await asyncio.gather(*tasks)
        return responses

    def update_test(self):
        log(f'[TEST] STARTING Sync @ {datetime.now().isoformat()}')
        url = self.env['ir.config_parameter'].sudo().get_param('instashop.url')
        api_key = self.env['ir.config_parameter'].sudo().get_param('instashop.api_key')
        conn = InstaConnector(api_key, url)

        # Example Details
        barcode = '635934607935'
        price = 3.4
        discount_price = 3.0
        status = 'in_stock'
        zallaq_branch_id = 'PetArabia-Zallaq'
        details = (barcode, price, discount_price, status)
        full_list = [details for x in range(7500)]
        
        res = conn.update_products(zallaq_branch_id, ExtBarcodeList(full_list))
        log(res) 

    # @api.model
    def update_stock_all(self):
        log(f'STARTING InstaShop Sync @ {datetime.now().isoformat()}')
        loc_id_to_instashop = {}
        insta_id_to_products_mapping = {}
        records = self.env['pos.config.instashop'].search([])
        if not records:
            _logger.error('No Point-of-Sales Configured for Instashop Sync, '
            'therefore an update is not going to happen.')
            return
        for rec in records:
            # Get Location ID from PoS Config ID
            location_id = rec.config_id.picking_type_id.warehouse_id.lot_stock_id.id
            if not location_id:
                _logger.error(_(f'There is no stock location assigned to Point of Sale: {rec.config_id.name}'))
                return
            loc_id_to_instashop[location_id] = rec.instashop_id
            insta_id_to_products_mapping[rec.instashop_id] = []
        
        LOCATION_IDS = list(loc_id_to_instashop.keys())
        LOCAION_IDS_AS_STR = ", ".join([str(id) for id in LOCATION_IDS])
        # Execute query
        query = self._read_sql_fromfile('run.sql').replace('{INSERT_LOCATION_IDS}', LOCAION_IDS_AS_STR)
        self.env.cr.execute(query)

        products_data = self.env.cr.dictfetchall()
        log(f'# of Products = {len(products_data)}')
        log(f'Received Products Data from Location IDs: {LOCAION_IDS_AS_STR}')

        product_ids = list(set([p['id'] for p in products_data]))
        product_prices = [p.lst_price for p in self.env['product.product'].browse(product_ids)]
        product_id_to_price =  dict(zip(product_ids, product_prices))
        log('Created the product IDS')
        for product in products_data:
            prod_price = product_id_to_price[product['id']]
            if product['id'] == 53408:
                log((product, prod_price))
            prod_barcode = product['barcode']
            product_available_loc_ids = product['location_ids']
            prod_loc_statuses = product['statuses']
            if prod_barcode == None:
                raise UserError('There are some products that have missing or invalid barcodes. Please check all barcodes and try this again.')

            for available_loc_id, prod_loc_status in zip(product_available_loc_ids, prod_loc_statuses):
                if not available_loc_id: # if product is Out-of-Stock in ALL Locations
                    continue
                # Get Insta ID
                insta_id = loc_id_to_instashop[available_loc_id]
                # Add to insta ID product updates
                prod_data = {
                        "price": str(prod_price),
                        "discountPrice": str(prod_price),
                        "plu": prod_barcode,
                        "barcode": prod_barcode,
                        "status": prod_loc_status
                    }
                insta_id_to_products_mapping[insta_id].append(prod_data)
            # Add disabled status for all other locations
            unavailable_loc_ids = set(LOCATION_IDS) - set(product_available_loc_ids)
            for unavailable_loc_id in unavailable_loc_ids:
                prod_data = {
                        "price": str(prod_price),
                        "discountPrice": str(prod_price),
                        "plu": prod_barcode,
                        "barcode": prod_barcode,
                        "status": "disabled"
                    }
                insta_id = loc_id_to_instashop[unavailable_loc_id]
                insta_id_to_products_mapping[insta_id].append(prod_data)
            
        log(f'Updating stock list now ....')
        responses = asyncio.run(self.publish_to_instashop(insta_id_to_products_mapping))
        for resp in responses:
            log(f"Unmatched Products Count: {resp[1]}")
        # log(responses)
        # log(f'Done Updating Batch {batch}')
        # batch +=1
        if not products_data:
            _logger.error('No products to sync')
        else:
            log('Synced with Instashop!')


        #POS -> Operation Type -> Warehouses -> Locations -> Quants (Product/Location) -> Product -> Product Quantity
        # product_id.stock_quant_ids
        # Product -> Quants
        
        # filter = available_in_pos, active

class InstashopProduct(models.Model):
    _inherit = 'product.product'
    available_on_instashop = fields.Boolean(
        default=False,
        string='Available on Instashop',
        tracking=True)

    def sync_with_instashop(self):
        for rec in self:
            rec.available_on_instashop = True

    def unsync_with_instashop(self):
        for rec in self:
            rec.available_on_instashop = False