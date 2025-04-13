# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _name = 'guazu.sale.order.line'
    _description = 'Sales Order Line'
    _order = 'order_id, sequence, id'

    @api.model
    def create(self, values):
        line = super(SaleOrderLine, self).create(values)
        return line

    @api.one
    @api.depends('quantity', 'price')
    def _compute_amount(self):
        self.amount = self.quantity * self.price

    @api.multi
    def write(self, values):
        result = super(SaleOrderLine, self).write(values)
        return result

    @api.one
    @api.depends('product_id', 'uom_id', 'track_id')
    def _get_product_existence(self):
        location_id = self.env.context.get('location_id', False)
        if location_id and self.product_id and self.uom_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_id)])
            if location.type == 'storage':
                # existence = self.product_id.get_existence_in_location(location_id, self.track_id.id)[0][0]
                existence = self.product_id.get_existence_in_location(location_id)[0][0]
                self.existence = self.product_id.uom_id._compute_quantity(existence, self.uom_id)
                return
        if self.product_id and self.uom_id:
            existence = self.product_id._get_existence()[0] or 0
            self.existence = self.product_id.uom_id._compute_quantity(existence, self.uom_id)
        else:
            self.existence = 0

    order_id = fields.Many2one('guazu.sale.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one('product.product', string='Producto', domain=[('sale_ok', '=', True)], ondelete='restrict', required=True)
    # product_id = fields.Many2one('product.template', string='Producto', domain=[('sale_ok', '=', True)],
    #                              ondelete='restrict', required=True)
    track_id = fields.Many2one('guazu.stock.track', string='Taller')
    uom_id = fields.Many2one('product.uom', string='UdM', required=True)
    price = fields.Monetary('Precio', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    quantity = fields.Float(string='Cantidad', digits=dp.get_precision('Product Unit of Measure'), required=True,
                            default=1.0)
    existence = fields.Float(string="Existencia", compute='_get_product_existence')
    amount = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Moneda', readonly=True)
    state = fields.Selection(string="Estado", related='order_id.state')

    @api.constrains('price', 'quantity')
    def _check_price(self):
        for record in self:
            if record.price < 0 or record.quantity < 0:
                raise VaidationError("Los valores de 'Precio' y 'Cantidad' no pueden ser negativo")


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'uom_id': []}}

        vals = {}
        domain = {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.uom_id or (self.product_id.uom_id.id != self.uom_id.id):
            vals['uom_id'] = self.product_id.uom_id
            vals['quantity'] = 1.0

        result = {'domain': domain}

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price'] = self.product_id.list_price

        self.update(vals)
        return result

    @api.onchange('uom_id')
    def product_uom_change(self):
        if not self.uom_id or not self.product_id:
            self.price = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            self.price = self.product_id.list_price
