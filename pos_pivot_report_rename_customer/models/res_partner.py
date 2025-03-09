from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        # print("name_get")

        res = []
        for partner in self:
            name = partner._get_name()

            if self.env.context.get('custom_pivot', False):
                if partner.phone:
                    res.append((partner.id, "{} {}".format(name, partner.phone)))
                elif partner.mobile:
                    res.append((partner.id, "{} {}".format(name, partner.mobile)))
                else:
                    res.append((partner.id, name))
                   
            else:
                res.append((partner.id, name))
            print("res1", res)
        return res
