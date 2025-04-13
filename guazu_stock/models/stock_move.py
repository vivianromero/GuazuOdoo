# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _
import datetime


class StockMove(models.Model):
    _name = "guazu.stock.move"
    _order = "emission_date desc, id desc"

    @api.depends('line_ids.amount')
    def _total_amount(self):
        for move in self:
            total_amount = 0.0
            for line in move.line_ids:
                total_amount += line.amount
            move.total_amount = total_amount

    @api.depends('line_ids.quantity')
    def _total_quantity(self):
        for move in self:
            total_qty = 0.0
            for line in move.line_ids:
                total_qty += line.quantity
            move.total_quantity = total_qty
            

    company_id = fields.Many2one('res.company', 'Compañía', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('guazu.stock.move'))
    name = fields.Char('Consecutivo', size=300, required=True, default="")
    origin = fields.Reference(string='Documento original', selection=[('guazu.sale.order', 'guazu.sale.order')], readonly=True)
    location_id = fields.Many2one('guazu.stock.location', string='Origen', required=True)
    location_dest_id = fields.Many2one('guazu.stock.location', string='Destino', required=True)
    emission_date = fields.Date(string="Fecha de emisión", copy=False, default=fields.Datetime.now, required=True)
    done_date = fields.Date(string="Fecha de terminación",required=True)
    note = fields.Text(string="Notas")
    product_id = fields.Many2one('product.product', 'Producto')
    line_ids = fields.One2many('guazu.stock.move.line', 'stock_move_id', 'Detalles')
    currency_id = fields.Many2one("res.currency", string="Moneda", related="company_id.currency_id", readonly=True, required=True)
    total_amount = fields.Monetary(string='Importe', store=True, readonly=True, compute='_total_amount',
                                   track_visibility='always')
    total_quantity = fields.Float(string='Cantidad', store=True, readonly=True, compute='_total_quantity',
                                   track_visibility='always')
    state = fields.Selection([('draft', 'Borrador'), ('wait', 'En espera'), ('done', 'Terminado'), ('cancel', 'Cancelado')],
                             default='draft', string="Estado", required=True)

    #_sql_constraints = [('name', 'unique (name)', "El nombre debe ser único.")]
    _sql_constraints = [
          ('name_location_id', 'unique (name,location_id,location_dest_id)', 'El nombre debe ser único para el origen y el destino.')
    ]
	        


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # todo improve this
        args2 = []
        product=False
        for arg in args:
            if arg[0]!="product_id":
                args2.append(arg)
            if arg[0]=="product_id":
                product = arg[2]
                
        moves = super(StockMove, self).search(args=args2, offset=offset, limit=limit, order=order, count=count)
        if not product:
            return moves
        
        move_ids = []
        for move in moves:
            for line in move.line_ids:
                if line.product_id.id == product:
                    move_ids.append(move.id)    
        return self.env["guazu.stock.move"].search([("id", "in", move_ids)])
        
    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')])
        return [(model.model, model.name)
                for model in models
                if not model.model.startswith('ir.')]

    @api.onchange('location_id')
    def onchange_location_id(self):
        self.line_ids = []

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') == ''):
            seq_obj_name = 'guazu.stock.move'
            vals['name'] = self.env['ir.sequence'].get(seq_obj_name)
        return super(StockMove, self).create(vals)

    @api.one
    def write(self, vals):
        if 'state' in vals:
            if not vals['state']:
                del vals['state']
        return super(StockMove, self).write(vals)

    @api.one
    def case_done(self):
        if not self.emission_date:
            raise exceptions.Warning(_('Debe asignar la fecha de emisión antes de terminar el movimiento'))
        if not self.done_date:
            self.done_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if self.done_date < self.emission_date:
            raise exceptions.Warning(_('La fecha de terminación no puede ser menor que la fecha de emisión'))

        if self.location_id == self.location_dest_id:
            raise exceptions.Warning(_('El origen y el destino no pueden ser iguales'))

        for line in self.line_ids:
            if line.quantity <= 0:
                raise exceptions.Warning(
                    'La cantidad a mover del producto "' + line.product_id.name + '" debe ser mayor que cero')
            if line.price < 0:
                raise exceptions.Warning(
                    'El precio unitario del producto "' + line.product_id.name + '" no puede ser menor que cero')

        # avoids to move too much quantity of product: just for outs
        if self.location_id.type == 'storage':
            for line in self.line_ids:
                if line.product_id.type == "product":
                    existence = line.product_id.get_existence_in_location(self.location_id.id, line.track_id.id)[0][0]
                    if round(line.quantity,2) > round(existence,2):
                        if line.track_id:
                            raise exceptions.Warning(_('No puede mover ') + str(line.quantity) + ' ' + line.uom_id.name +
                                                 _(' del producto ') + line.product_id.name + _('. La existencia es sólo ') +
                                                 str(existence) + ' ' + line.uom_id.name +' (Para el taller ' + line.track_id.name +')')
                        else:
                            raise exceptions.Warning(_('No puede mover ') + str(line.quantity) + ' ' + line.uom_id.name +
                                                 _(' del producto ') + line.product_id.name + _('. La existencia es sólo ') +
                                                 str(existence) + ' ' + line.uom_id.name)
                # re calculate prices auto
                qty = line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                new_std_price = line.uom_id._compute_price(line.product_id.standard_price, line.product_id.uom_id)
                line.write({'price': new_std_price, 'amount': new_std_price * qty})

        # Average price computation
        if self.location_dest_id.type == 'storage':
            for line in self.line_ids:
                qty = line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                if qty > 0:
                    new_price = line.uom_id._compute_price(line.price, line.product_id.uom_id)

                    if line.product_id.existence <= 0:
                        new_std_price = new_price
                    else:
                        # Get the standard price
                        amount_unit = line.product_id.price_get('standard_price')[line.product_id.id]
                        new_std_price = ((amount_unit * line.product_id.existence)\
                                         + (new_price * qty)) / (line.product_id.existence + qty)

                    # Write the field according to price type field
                    line.product_id.write({'standard_price': new_std_price})

        self.write({'state': 'done'})

    @api.one
    def case_cancel(self):
        self.write({'state': 'cancel'})

    @api.one
    def unlink(self):
        if self.state not in ('draft',):
            raise exceptions.Warning(_('Sólo se pueden eliminar movimientos de inventario en estado borrador'))

        super(StockMove, self).unlink()

    @api.multi
    def action_open_report_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s' % ('guazu_stock.report_stock_move_invoice', self.id),
        }

    @api.multi
    def action_open_report_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s' % ('guazu_stock.report_stock_move', self.id),
        }

    @api.onchange('emission_date')
    def _onchange_emission_date(self):
        if self.emission_date:
            self.done_date = self.emission_date
