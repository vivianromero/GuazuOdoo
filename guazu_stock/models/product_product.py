# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _

import operator as py_operator
OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = "product.product"

    @api.one
    def _get_existence(self):
        existence = 0
        lines = self.env['guazu.stock.move.line'].search([('product_id', '=', self.id)])

        location_name = self.env.context.get('location', False)
        if location_name:
            if isinstance(location_name, (int, long)):
                location_ids = [location_name]
            elif isinstance(location_name, (str, unicode)):
                domain = [('name', 'ilike', location_name)]
                location_ids = [loc.id for loc in self.env['guazu.stock.location'].search(domain)]
            else:
                location_ids = self.env.context['location']
            for line in lines:
                if line.stock_move_id.state == 'done':
                    if line.stock_move_id.location_dest_id.id in location_ids:
                        existence += line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    if line.stock_move_id.location_id.id in location_ids:
                        existence -= line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
        else:
            for line in lines:
                if line.stock_move_id.state == 'done':
                    if line.stock_move_id.location_dest_id.type == 'storage':
                        existence += line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    if line.stock_move_id.location_id.type == 'storage':
                        existence -= line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)

        self.existence = existence
        return existence

    @api.one
    def get_existence_in_location(self, location_id, track_id=False):
        existence = amount = 0
        lines = self.env['guazu.stock.move.line'].search([('state', '=', 'done'),('product_id', '=', self.id)])
        for line in lines:
            if track_id:
                if line.stock_move_id.location_dest_id.id == location_id and line.track_id.id == track_id:
                    existence += line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    amount += line.amount
                if line.stock_move_id.location_id.id == location_id and line.track_id.id == track_id:
                    existence -= line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    amount -= line.amount
            else:
                if line.stock_move_id.location_dest_id.id == location_id:
                    existence += line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    amount += line.amount
                if line.stock_move_id.location_id.id == location_id:
                    existence -= line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                    amount -= line.amount
        return existence, amount

    def _search_product_quantity(self, operator, value):
        # TDE FIXME: should probably clean the search methods
        # to prevent sql injections
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise exceptions.UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise exceptions.UserError(_('Invalid domain right operand %s') % value)

        # TODO: Still optimization possible when searching virtual quantities
        ids = []
        for product in self.search([]):
            if OPERATORS[operator](product['existence'], value):
                ids.append(product.id)
        return [('id', 'in', ids)]

    def _search_existence(self, operator, value):
        domain = [('existence', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    #_sql_constraints = [('default_code, product_tmpl_id', 'unique (default_code)',
    #                     "El código del producto debe ser único.")]

    existence = fields.Float(compute=_get_existence, string="Existencia", search='_search_product_quantity')
    
    @api.model
    def create(self, vals):
        if not vals.get('default_code', False):
            if vals.get('product_tmpl_id', False):
                template = self.env['product.template'].browse(vals.get('product_tmpl_id', False))
                vals.update({'default_code': template.default_code})
        return super(ProductProduct, self).create(vals)

    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        new_args = []
        for arg in args:
            if arg[0] == "location_id":
                arg[1] = '='
                arg[2] = None
            new_args.append(arg)

        return super(ProductProduct, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
