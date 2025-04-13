# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _
from odoo.addons import decimal_precision as dp

def float_round(number, digits):
    return number * pow(10, digits) / pow(10, digits)

class StockMoveLine(models.Model):
    _name = "guazu.stock.move.line"

    def default_auto_price(self):
        location_id = self.env.context.get('location_id', False)
        if location_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_id)])
            if location.type == 'storage':
                return True
        return False

    @api.one
    @api.depends('product_id', 'uom_id', 'track_id')
    def _get_product_existence(self):
        location_id = self.env.context.get('location_id', False)
        if location_id and self.product_id and self.uom_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_id)])
            if location.type == 'storage':
                existence = self.product_id.get_existence_in_location(location_id, self.track_id.id)[0][0]
                self.existence = self.product_id.uom_id._compute_quantity(existence, self.uom_id)
                return
        location_dest_id = self.location_dest_id
        if location_dest_id and self.product_id and self.uom_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_dest_id.id)])
            if location.type == 'storage':
                existence = self.product_id.get_existence_in_location(location_dest_id.id, self.track_id.id)[0][0]
                self.existence = self.product_id.uom_id._compute_quantity(existence, self.uom_id)
                return
        self.existence = 0

    @api.one
    @api.depends('product_id', 'quantity', 'existence')
    def _get_existence_final(self):
        location_id = self.location_id
        if location_id and self.product_id and self.uom_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_id.id)])
            if location.type == 'storage':
                self.existence_final = self.existence - self.quantity
                return

        location_dest_id = self.location_dest_id
        if location_dest_id and self.product_id and self.uom_id:
            location = self.env['guazu.stock.location'].search([('id', '=', location_dest_id.id)])
            if location.type == 'storage':
                self.existence_final = self.existence + self.quantity
                return
        self.existence_final = 0

    """@api.onchange('use_tracks')
    def onchange_use_tracks(self):
        if !self.use_tracks:"""

    stock_move_id = fields.Many2one('guazu.stock.move', string='Movimiento', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    use_tracks = fields.Boolean('Dar seguimiento', related='product_id.use_tracks')
    track_id = fields.Many2one('guazu.stock.track', string='Taller')
    uom_id = fields.Many2one('product.uom', string='UdM', required=True)
    quantity = fields.Float(string="Cantidad", digits=(16,2), required=True, default=0)
    existence = fields.Float(string="Existencia", digits=(16,2), compute='_get_product_existence')
    currency_id = fields.Many2one("res.currency", string="Moneda", related="stock_move_id.currency_id", readonly=True, required=False)
    price = fields.Float(string="Precio unitario", digits=(16,5), required=True, default=0)
    amount = fields.Float(string="Importe", digits=(16,2), required=True, default=0)
    done_date = fields.Date(string="Fecha de terminación", realted="stock_move_id.done_date")
    location_id = fields.Many2one('guazu.stock.location', string='Origen', related="stock_move_id.location_id")
    location_dest_id = fields.Many2one('guazu.stock.location', string='Destino', related="stock_move_id.location_dest_id")

    auto_price = fields.Boolean(string="Precio automático", default=default_auto_price)
    state = fields.Selection(string="Estado", related='stock_move_id.state')
    existence_final = fields.Float(string="Existencia final", digits=(16, 2), compute='_get_existence_final')

    @api.onchange('quantity', 'price')
    def calculate_new_amount(self):
        self.amount = float_round(float_round(self.quantity,2) * float_round(self.price,5),2)

    @api.onchange('product_id')
    def onchange_product(self):
        self.track_id = False
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.price = self.product_id.standard_price
        else:
            self.uom_id = False
            self.price = 0

    @api.onchange('uom_id')
    def onchange_uom(self):
        if self.uom_id:
            product_uom = self.product_id.uom_id
            if self.uom_id.category_id != product_uom.category_id:
                raise exceptions.Warning(_("Sólo se permiten unidades de medida de '%s'") % product_uom.category_id.name)
            if self.auto_price:
                self.price = self.product_id.uom_id._compute_price(self.product_id.standard_price, self.uom_id)

    @api.multi
    def write(self, vals):
        product = self.env['product.product'].browse(vals.get('product_id', self.product_id.id))
        use_tracks = product.use_tracks
        if use_tracks and not vals.get('track_id', self.track_id):
            raise exceptions.Warning('El producto %s tiene seguimiento. Debe especificar el taller de procedencia.' % product.name_get()[0][1]) 
        if not use_tracks and vals.get('track_id', self.track_id):
            raise exceptions.Warning('El producto %s no tiene seguimiento. No debe especificar el taller de procedencia.' % product.name_get()[0][1]) 
            
        uom = self.env['product.uom'].browse(vals.get('uom_id', self.uom_id.id))
        quantity = vals.get('quantity', self.quantity)
        quantity = float_round(quantity, 2)
        auto_price = vals.get('auto_price', self.auto_price)
        if product.uom_id.category_id != uom.category_id:
            raise exceptions.Warning(_("Sólo se permiten unidades de medida de '%s' para el producto '%s'") % (product.uom_id.category_id.name, product.name))

        if auto_price:
            price = product.uom_id._compute_price(product.standard_price, uom)
        else:
            price = vals.get('price', self.price)
        price = float_round(price, 5)
        vals.update({'price': price, 'amount': float_round(quantity * price, 2)})
        return super(StockMoveLine, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('product_id', False):
            product = self.env['product.product'].browse(vals.get('product_id'))
            use_tracks = product.use_tracks
            if use_tracks and not vals.get('track_id', False):
                raise exceptions.Warning('El producto %s tiene seguimiento. Debe especificar el taller de procedencia.' % product.name_get()[0][1]) 
            if not use_tracks and vals.get('track_id', False):
                raise exceptions.Warning('El producto %s no tiene seguimiento. No debe especificar el taller de procedencia.' % product.name_get()[0][1]) 
            uom = self.env['product.uom'].browse(vals.get('uom_id'))
            quantity = vals.get('quantity')
            quantity = float_round(quantity, 2)
            auto_price = vals.get('auto_price', False)
            if product.uom_id.category_id != uom.category_id:
                raise exceptions.Warning(
                    _("Sólo se permiten unidades de medida de '%s' para el producto '%s'") % (product.uom_id.category_id.name,
                    product.name))

            if auto_price:
                price = product.uom_id._compute_price(product.standard_price, uom)
            else:
                price = vals.get('price')
            price = float_round(price, 5)
            vals.update({'price': price, 'amount': float_round(quantity * price, 2)})

        return super(StockMoveLine, self).create(vals)

