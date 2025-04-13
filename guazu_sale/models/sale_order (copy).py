# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, AccessError,ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = "guazu.sale.order"
    _description = "Quotation"
    _order = 'create_date desc, id desc'

    @api.depends('line_ids.amount')
    def _amount_all(self):
        for order in self:
            amount_total = 0.0
            for line in order.line_ids:
                amount_total += line.amount
            order.update({'amount_total': amount_total})

    @api.depends('line_ids.quantity')
    def _quantity_all(self):
        for order in self:
            qty_total = 0.0
            for line in order.line_ids:
                qty_total += line.quantity
            order.update({'quantity_total': qty_total})

    def _get_location_default(self):
        location_id = self.env["ir.config_parameter"].sudo().get_param('guazu_sale.warehouse_id')
        if location_id:
            return self.env["guazu.stock.location"].search([('id', '=', location_id)])
        return False

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Oferta'),
        ('sent', 'Oferta enviada'),
        ('register','Registrada'),
        ('confirmed', 'Confirmada'),
        ('invoiced', 'Facturada'),
        # ('done', 'Terminada'),
        ('cancel', 'Cancelada'),
        ('cancelnotback', 'Cancelada'),
        ('pay','Pagada'),
        ], string='Estado', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Archivo Adjunto'
    )
    validity_date = fields.Date(string='Fecha de caducidad', readonly=True, copy=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    is_late = fields.Boolean(compute='_compute_is_late', search='_search_is_late', string="Demorada")
    create_date = fields.Datetime(string='Fecha de creación', readonly=True, index=True, help="Date on which sales order is created.")
    confirmation_date = fields.Datetime(string='Fecha de confirmación', readonly=True, index=True, help="Date on which the sales order is confirmed.", oldname="date_confirm")
    picking_date = fields.Date(string='Fecha de entrega', index=True, help="Fecha esperada para entregar los productos")
    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
    pricelist_id = fields.Many2one('product.pricelist', string='Tarifa de precios', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Tarifa de precios para esta venta.")
    currency_id = fields.Many2one("res.currency", related='company_id.currency_sales_id', string="Moneda", readonly=True, required=True)
    line_ids = fields.One2many('guazu.sale.order.line', 'order_id', string='Detalles', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    note = fields.Text('Observaciones')
    amount_total = fields.Monetary(string='Importe total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    quantity_total = fields.Float(string='Cantidad total', store=True, readonly=True, compute='_quantity_all',
                                   track_visibility='always')
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env['res.company']._company_default_get('guazu.sale.order'))
    location_id = fields.Many2one('guazu.stock.location', string="Almacén de venta", domain=[('type', '=', 'storage')], default=_get_location_default,
                                  readonly=True, copy=False, states={'draft': [('readonly', False)]})
    # stock_move_id = fields.Many2one('guazu.stock.move', string='Movimiento de inventario', readonly=True, required=False)
    # department_id = fields.Many2one('hr.department', domain=[('parent_id', '!=', False)], string='Grupo', required=False)
    # employee_ids=fields.Many2many("guazu.hr.employee", "guazu_sales_employee_rel", "employee_id", "order_id",
    #                  string="Artesanos a pagar",required=False)
    nro_contrato = fields.Char(string="Código REUP", size=25)
    nro_invoice = fields.Char(string="Nro. Factura", size=25, readonly=True, states={'confirmed': [('readonly', False)]})

    def _compute_is_late(self):
        now = datetime.now()
        for order in self:
            if order.state in ("draft", "sent", "register"):
                if order.validity_date and fields.Datetime.from_string(order.validity_date) < now:
                    order.is_late = True
                else:
                    order.is_late = False

            if order.state in ("confirmed", "invoiced"):
                if order.picking_date and fields.Datetime.from_string(order.picking_date) < now:
                    order.is_late = True
                else:
                    order.is_late = False

    @api.multi
    def _search_is_late(self, operator, value):
        res = []
        orders = self.search([])
        for order in orders:
            if order.is_late:
                res.append(order.id)

        return [('id', 'in', res)]

    @api.multi
    def unlink(self):
        for order in self:
            if order.state in ('pay'):
                raise UserError(_('No puede borrar una orden de venta que ya ha sido pagada!'))
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('No puede borrar una orden de venta o una oferta enviada! Debe cancelarla primero.'))
        return super(SaleOrder, self).unlink()

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            for line in self.line_ids:
                line.existence = line.product_id.get_existence_in_location(self.location_id.id)[0][0]

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        #verificar que no este registrada
        payment_obj = self.env['guazu.payment']
        cond = [('sale_order_id.name', '=', self.name)]
        payments = payment_obj.search(cond)
        exist_payment = False
        for payment in payments:
            exist_payment = True
            self.partner_id = payment.partner_id
        if not self.partner_id:
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False
        }
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note
        self.update(values)
        if exist_payment:
            res={}
            self.partner_id = payment.partner_id
            res['warning'] = {'title': _('Warning'), 'message': _(
                'No puede cambiar el cliente. Esta orden de venta está registrada')}
            return res

    @api.model
    def create(self, vals):
        _logger.warning("estoy en create")
        if not len(vals.get('line_ids', [])):
            raise UserError(_('Debe añadir al menos un producto.'))
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.order') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or _('New')

        # Makes sure 'pricelist_id' are defined
        if any(f not in vals for f in ['pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result

    @api.multi
    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'line_ids' not in default:
            default['line_ids'] = [(0, 0, line.copy_data()[0]) for line in self.line_ids.filtered(lambda l: not l.is_downpayment)]
        return super(SaleOrder, self).copy_data(default)

    @api.multi
    def name_get(self):
        if self._context.get('sale_show_partner_name'):
            res = []
            for order in self:
                name = order.name
                if order.partner_id.name:
                    name = '%s - %s' % (name, order.partner_id.name)
                res.append((order.id, name))
            return res
        return super(SaleOrder, self).name_get()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('sale_show_partner_name'):
            if operator in ('ilike', 'like', '=', '=like', '=ilike'):
                domain = expression.AND([
                    args or [],
                    ['|', ('name', operator, name), ('partner_id.name', operator, name)]
                ])
                return self.search(domain, limit=limit).name_get()
        return super(SaleOrder, self).name_search(name, args, operator, limit)

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        #return self.env['report'].get_action(self, 'guazu_sale.report_saleorder', data=None)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s' % ('guazu_sale.report_saleorderotro', self.id),
        }
        # odoo 11
        # return self.env.ref('guazu_sale.action_report_saleorder').report_action(self)

    @api.multi
    def action_view_invoice(self):
        _logger.warning("estoy en action_view_invoice")
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_draft(self):
        _logger.warning("estoy en action_draft")
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'cancelnotback'])
        return orders.write({
            'state': 'draft',
        })

    @api.multi
    def action_send(self):
        _logger.warning("estoy en action_send")
        sales_line_obj = self.env['guazu.sale.order.line']
        cond = [('order_id', '=', self.id)]
        lines = sales_line_obj.search(cond)
        if lines.__len__() == 0:
            raise UserError(_('Debe añadir al menos un producto.'))

        for line in lines:
            if line.price == 0.0:
                raise UserError(_('No puede ser Enviada existen productos con precio 0.00'))
            if line.quantity <= 0.0:
                raise UserError(_('No puede ser Enviada existen productos con cantidad incorrecta'))


        payment_obj = self.env['guazu.payment']
        cond = [('sale_order_id', '=', self.id)]
        payments = payment_obj.search(cond)
        for payment in payments:
            payment.state = 'draft'
        return self.write({'state': 'sent'})

    @api.multi
    def action_cancel(self):
        _logger.warning("estoy en action_cancel")
        _logger.warning(self.state)
        payment_obj = self.env['guazu.payment']
        cond = [('sale_order_id', '=', self.id)]
        payments = payment_obj.search(cond)

        state = 'cancel' if self.state != 'invoiced' else 'cancelnotback'

        for payment in payments:
            payment.state = 'cancel'
            state='cancelnotback'
        return self.write({'state': state,
                           'nro_invoice': '' if state == 'cancel' else self.nro_invoice})

    @api.multi
    def action_done(self):
        _logger.warning("estoy en action_done")
        # crear los movimientos de inventarios necesarios
        location_dest_id = self.env["ir.config_parameter"].sudo().get_param('guazu_sale.location_id')

        stock_move = self.env["guazu.stock.move"].sudo().create(
            {'location_id': self.location_id.id,
             'location_dest_id': location_dest_id,
             'origin': self._name + ',' + str(self.id),
             'done_date': fields.Datetime.now(),
             'note': "Vale de salida de la orden de venta " + self.name,
             'state': 'draft'})
        for line in self.line_ids:
            self.env['guazu.stock.move.line'].sudo().create({'stock_move_id': stock_move.id,
                                                      'product_id': line.product_id.id,
                                                      'uom_id': line.uom_id.id,
                                                      'track_id': line.track_id.id,
                                                      'price': line.product_id.standard_price,
                                                      'amount': line.product_id.standard_price * line.quantity,
                                                      'auto_price': True,
                                                      'quantity': line.quantity})
        stock_move.sudo().case_done()
        self.write({'state': 'done', 'stock_move_id': stock_move.id})

    @api.multi
    def action_invoice(self):
        _logger.warning("estoy en action_invoice")
        if not self.nro_invoice:
            raise UserError(_('Debe introducir el número de la Factura.'))
        self.write({'state': 'invoiced'})

    @api.multi
    def action_confirm(self):
        _logger.warning("estoy en action_confirm")
        now = datetime.now()
        # if self.state != 'register':
        #     raise exceptions.Warning(_('No se puede Confirmar la Venta, aún no se ha registrado'))
        if not self.partner_id.number_contract:
            raise exceptions.Warning(_('No se puede Confirmar la Venta, el cliente no tiene contrato'))
        if not self.partner_id.expire_contract_date:
            raise exceptions.Warning(_('No se puede Confirmar la Venta, el contrato no tiene fecha de vencimiento'))
        if fields.Datetime.from_string(self.partner_id.expire_contract_date)<now:
            raise exceptions.Warning(_('No se puede Confirmar la Venta, el contrato ha expirado'))
        if not self.partner_id.reup:
            raise exceptions.Warning(_('No se puede Confirmar la Venta, el cliente no tiene el Código REUP'))


        for line in self.line_ids:
            if line.quantity > line.existence:
                raise exceptions.Warning(_('No puede mover ') + str(line.quantity) + ' ' + line.uom_id.name +
                                         _(' del producto ') + line.product_id.display_name + _('. La existencia es sólo ') +
                                         str(line.existence) + ' ' + line.uom_id.name)
                # raise exceptions.Warning(
                #     'La cantidad a mover del producto "' + line.product_id.name + '" debe ser mayor que cero')
            if line.price < 0:
                raise exceptions.Warning(
                    'El precio unitario del producto "' + line.product_id.name + '" no puede ser menor que cero')
        self.write({
            'state': 'confirmed',
            'nro_contrato':self.partner_id.number_contract,
            'confirmation_date': fields.Datetime.now()
        })

        return True
    
    @api.multi
    def action_open_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s' % ('guazu_sale.report_saleorder', self.id),
        }
