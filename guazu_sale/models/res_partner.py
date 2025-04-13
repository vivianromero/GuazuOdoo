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
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _name = 'res.partner'

    org_id = fields.Many2one('guazu.partner.org', 'Organismo')
    reup = fields.Char(string="Código REUP", size=15)
    number_contract = fields.Char(string="Número", size=25)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='# de Ventas')
    expire_contract_date = fields.Date(string="Fecha de vencimiento")
    # sale_order_ids = fields.Many2many('guazu.sale.order',"guazu_sales_employee_rel", "order_id","employee_id", 'Órdenes de venta')

    # employee_ids = fields.Many2many("guazu.hr.employee", "guazu_sales_employee_rel", "employee_id", "order_id",
    #                                 string="Artesanos a pagar", required=False)
    #sale_warn = fields.Selection(WARNING_MESSAGE, 'Sales Order', default='no-message', help=WARNING_HELP, required=True)
    #sale_warn_msg = fields.Text('Message for Sales Order')

    def _compute_sale_order_count(self):
        sale_data = self.env['guazu.sale.order'].read_group(domain=[('partner_id', 'child_of', self.ids)],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in sale_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            item = next(p for p in partner_child_ids if p['id'] == partner.id)
            partner_ids = [partner.id] + item.get('child_ids')
            # then we can sum for all the partner's child
            partner.sale_order_count = sum(mapped_data.get(child, 0) for child in partner_ids)
