from odoo.exceptions import ValidationError
from odoo import models


class PaymentAcquirerStripe(models.Model):
    _inherit = 'payment.acquirer'

    def _stripe_request(self, *args, **kw):
        try:
            return super()._stripe_request(*args, **kw)
        except ValidationError as error_msg:
            error_msg = str(error_msg).replace('Stripe gave us', 'We received')
            raise ValidationError(error_msg)

