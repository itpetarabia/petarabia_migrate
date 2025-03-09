from odoo import models, fields,api
logo_size = {'height':100,'width':100}

class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.onchange('show_company_name_receipt')
    def onchange_show_company_name_receipt(self):
        if self.show_company_name_receipt:
            self.company_name_receipt = self.company_id.name
    
    #receipt attributes
    logo = fields.Binary(string='Logo')
    show_company_name_receipt = fields.Boolean("Show Company Name",default=True)
    company_name_receipt = fields.Char("Receipt Company Name")

    show_company_address_receipt = fields.Boolean("Show Company Address",default=True)
    company_address_receipt = fields.Text("Company Address")

    show_vat_no_receipt = fields.Boolean("Show Vat No",default=True)
    vat_no_receipt = fields.Char("Vat No")
    show_logo_receipt = fields.Boolean("Show Logo",default=True)
    title_receipt = fields.Char(string="Receipt Title",default='TAX INVOICE')
    logo_width_receipt = fields.Float("Logo Width (Pixel)",default=logo_size['width'])
    logo_height_receipt = fields.Float("Logo Height (Pixel)",default=logo_size['height'])

    show_vat_summary_receipt = fields.Boolean("Show VAT Summary",default=True)
    show_cashier_receipt = fields.Boolean("Show Cashier Name", default=True)
    show_customer_receipt = fields.Boolean("Show Customer Details", default=False)

    font_size_receipt = fields.Float("Receipt Whole Font Size (PX)",default=14)
    
    @api.onchange('logo_height_receipt')
    def onchange_logo_height(self):
        if self.logo_height_receipt <= 0:
            self.logo_height_receipt = logo_size['height']
            
    @api.onchange('logo_width_receipt')
    def onchange_logo_width_receipt(self):
        if self.logo_width_receipt <= 0:
            self.logo_width_receipt = logo_size['width']
        
        
