from odoo import models, _, fields, api
from datetime import datetime, timedelta, date
import calendar
from odoo.exceptions import except_orm, Warning, RedirectWarning
from lxml import etree
from odoo.tools import float_utils
from odoo.exceptions import UserError, AccessError


class PaymentLine(models.Model):
    _name = "guazu.payment.line"

    @api.one
    @api.depends('amount', 'discount')
    def _compute_net(self):
        self.net = float_utils.float_round(self.amount - self.discount,2)

    @api.one
    @api.depends('payment_id.onat','net')
    def _compute_onat(self):
        self.tax = float_utils.float_round((self.net * self.payment_id.onat)/100,2)

    @api.one
    @api.depends('tax', 'net')
    def _compute_receive(self):
        self.receive = float_utils.float_round(self.net-self.tax, 2)

    payment_id = fields.Many2one("guazu.payment", "Cobro", index=True, ondelete="cascade", required=True)
    employee_id = fields.Many2one("hr.employee", "Artesano", index=True, ondelete="restrict", required=True)
    currency_id = fields.Many2one("res.currency", string="Moneda", related="payment_id.currency_id", readonly=True,
                                  required=False)
    amount = fields.Monetary(string="Ventas", required=True, default=0)
    discount = fields.Monetary("Aporte al Fondo", required=True, default=0)
    # tax = fields.Monetary(string="Impuesto", required=True, default=0)
    net = fields.Monetary(string="Neto", compute=_compute_net, store=True)
    tax = fields.Monetary(string="% ONAT", compute=_compute_onat, store=True)
    receive = fields.Monetary(string="A Cobrar", compute=_compute_receive, store=True)








