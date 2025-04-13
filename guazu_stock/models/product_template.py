# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api
#from odoo.tools import pycompat


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = "product.template"
    _order = "default_code asc"

    @api.one
    def _get_move_count(self):
        #lines = self.env["guazu.stock.move.line"].search([('product_id', '=', self.id)])
        query = """select count(move.id) from 
            guazu_stock_move move left join guazu_stock_move_line line on (line.stock_move_id = move.id)
            left join product_product product on (line.product_id = product.id)
            where line.product_id = """ + str(self.id)
        self.env.cr.execute(query)
        data = self.env.cr.dictfetchall()
        
        self.move_count = data[0]['count'] or 0

    type = fields.Selection(selection_add=[('product', 'Almacenable')])
    location_id = fields.Many2one('guazu.stock.location', 'Ubicación')
    move_count = fields.Integer(compute=_get_move_count, string="Movimientos")
    color_id = fields.Many2one('guazu.product.color', 'Color')
    color_image = fields.Binary(related="color_id.image")
    material_id = fields.Many2one('guazu.product.material', 'Material')
    material_image = fields.Binary(related="material_id.image")
    sex_id = fields.Many2one('guazu.product.sex', 'Sexo')
    sex_image = fields.Binary(related="sex_id.image")
    use_tracks = fields.Boolean('Dar seguimiento', default=False)
    product_variant_ids = fields.One2many('product.product', 'product_tmpl_id', 'Products', required=True)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True)
    list_price = fields.Float(string='Sale Price', default=0.0)
    
    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.default_code = template.product_variant_ids.default_code
        for template in (self - unique_variants):
            for variant in template.product_variant_ids:
                template.default_code = variant.default_code

    @api.one
    def _set_default_code(self):
        for variant in self.product_variant_ids:
            variant.write({'default_code': self.default_code})

    @api.one
    def _get_existence(self):
        existence = 0
        variants = []
        for variant in self.product_variant_ids:
            variants.append(variant.id)
        lines = self.env['guazu.stock.move.line'].search([('product_id', 'in', variants)])

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

    existence = fields.Float(compute=_get_existence, string="Existencia", search='_search_existence')

    @api.one
    def get_existence_in_location(self, location_id):
        existence = amount = 0
        variants = []
        for variant in self.product_variant_ids:
            variants.append(variant.id)
        lines = self.env['guazu.stock.move.line'].search([('product_id', 'in', variants)])
        for line in lines:
            if line.stock_move_id.state == 'done' and line.stock_move_id.location_dest_id.id == location_id:
                existence += line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                amount += line.amount
            if line.stock_move_id.state == 'done' and line.stock_move_id.location_id.id == location_id:
                existence -= line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                amount -= line.amount

        return existence, amount

    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_standard_price(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.standard_price = template.product_variant_ids.standard_price
        for template in (self - unique_variants):
            existence = 0
            amount = 0
            for variant in template.product_variant_ids:
                amount += variant.existence * variant.standard_price
                existence += variant.existence
            if existence:
                template.standard_price = amount / existence
            else:
                template.standard_price = 0.0

    def _search_existence(self, operator, value):
        domain = [('existence', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        new_args = []
        for arg in args:
            if arg[0] != "location_id":
                new_args.append(arg)
        return super(ProductTemplate, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
