# Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
# Copyright 2018 Artem Losev
# License MIT (https://opensource.org/licenses/MIT).

from odoo import api, fields, models

CHANNEL = "pos_orders_history_receipt"


class PosConfig(models.Model):
    _inherit = "pos.config"
    reprint_orders = fields.Boolean(
        "Reprint Orders",
        help="Reprint paid POS Orders with POS interface",
        default=True,
    )

    """# ir.actions.server methods:
    @api.model
    def notify_receipt_updates(self):
        ids = self.env.context["active_ids"]
        if len(ids):
            message = {"updated_receipts": ids}
            self.search([])._send_to_channel(CHANNEL, message)"""


"""class PosReceipt(models.Model):
    _name = "pos.xml_receipt"
    _description = "XML Receipt"

    receipt = fields.Char("Receipt")
    pos_reference = fields.Char("Reference")
    #receipt_type = fields.Selection(
    #    [("xml", "XML"), ("ticket", "Ticket")], "Receipt Type"
    #)

    #def save_xml_receipt(self, name, receipt, receipt_type):
    #    self.create(
    #        {"pos_reference": name, "receipt": receipt, "receipt_type": receipt_type}
    #    )
    def save_xml_receipt(self, name, receipt):
        self.create(
            {"pos_reference": name, "receipt": receipt}
        )"""
