# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, _, fields, api
from datetime import datetime, timedelta, date
import calendar
from odoo.exceptions import except_orm, Warning, RedirectWarning
from lxml import etree


class OrderLine(models.Model):
    _name = "guazu.mrp.order.line"

    order_id = fields.Many2one("guazu.mrp.order", "Orden", index=True, ondelete="cascade", required=True)
    employee_id = fields.Many2one("hr.employee", "Empleado", index=True, ondelete="restrict", required=True)
    activity_id = fields.Many2one("guazu.mrp.activity", "Operación", index=True, ondelete="restrict", required=True, domain="[('workshop_id', '=', order_id.workshop_id.id)]")
    currency_id = fields.Many2one("res.currency", string="Moneda", related="order_id.currency_id", readonly=True,
                                  required=False)
    price = fields.Monetary(string="Precio", required=True, default=0)
    amount = fields.Monetary(string="Importe", required=True, default=0)
    quantity = fields.Integer("Cantidad")

    @api.onchange('activity_id')
    def _onchange_activity(self):
        if self.activity_id:
            self.price = self.activity_id.price
        else:
            self.price = 0

    @api.onchange('quantity', 'price')
    def calculate_new_amount(self):
        self.amount = self.quantity * self.price

    @api.multi
    def write(self, vals):
        quantity = vals.get('quantity', self.quantity)
        activity = self.env['guazu.mrp.activity'].browse(vals.get('activity_id', self.activity_id.id))
        price = activity.price
        vals.update({'price': price, 'amount': quantity * price})
        return super(OrderLine, self).write(vals)

    @api.model
    def create(self, vals):
        activity = self.env['guazu.mrp.activity'].browse(vals.get('activity_id'))
        quantity = vals.get('quantity')
        price = activity.price
        vals.update({'price': price, 'amount': quantity * price})
        return super(OrderLine, self).create(vals)




