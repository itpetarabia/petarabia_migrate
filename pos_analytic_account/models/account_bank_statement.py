# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.exceptions import UserError

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def button_post(self):
        ''' Move the bank statements from 'draft' to 'posted'. '''
        if any(statement.state != 'open' for statement in self):
            raise UserError(_("Only new statements can be posted."))
        statements = self.sudo().filtered(lambda s: s.pos_session_id and s.pos_session_id.config_id.analytic_account_id)
        for statement in statements:
            for st_line in statement.line_ids:
                st_line.move_id.line_ids.write({'analytic_account_id': statement.pos_session_id.config_id.analytic_account_id.id})
        super(AccountBankStatement, self).button_post()