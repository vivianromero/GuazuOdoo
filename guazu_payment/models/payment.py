# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp

class SaleOrder(models.Model):
    _name = "guazu.sale.order"
    _inherit = "guazu.sale.order"

    payment_id = fields.Many2one('guazu.payment', readonly=True, string='pago', required=False)



class Payment(models.Model):
    _name = "guazu.payment"
    _description = "Payment"
    _order = 'date desc, id desc'

    @api.one
    @api.depends('sale_order_id','sale_order_id.amount_total')
    def _compute_sales_amount(self):
        self.sales_amount = 0
        for order in self.sale_order_id:
            self.sales_amount += order.amount_total
    
    @api.depends('line_ids')
    def _amount_all(self):
        for payment in self:
            amount_total = 0.0
            tax_total = 0.0
            net_total = 0.0
            for line in payment.line_ids:
                amount_total += line.amount
                tax_total += line.tax
                net_total += line.net
            payment.update({'amount_total': amount_total, 'tax_total': tax_total,'net_total': net_total})

    @api.one
    @api.depends('payment_amount', 'discount')
    def _compute_distributable(self):
        self.distributable_amount = self.payment_amount - self.discount

    name = fields.Char("Número", required=True)
    company_id = fields.Many2one('res.company', 'Compañía', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('guazu.payment'))
    partner_id = fields.Many2one("res.partner", "Cliente", index=True, ondelete="restrict", required=True)
    date = fields.Date(string="Fecha", index=True, required=True, copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one("res.currency", string="Moneda", related="company_id.currency_sales_id", readonly=True,
                                  required=True)
    filial_id = fields.Many2one('guazu.payment.filial', 'Filial', ondelete="restrict", required=True)
    sale_order_id = fields.Many2one('guazu.sale.order', 'Ordenes de venta',
                                 required=True,domain="[('amount_paid', '<' ,'amount_total'), ('partner_id', '=', partner_id), ('state', '=', 'sent')]")
    # sale_order_ids = fields.Many2many("guazu.sale.order", "guazu_sale_order_payment_rel", "sale_order_id", "payment_id
    #                                   domain="[('partner_id', '=', partner_id), ('state', '=', 'invoiced'), ('amount_receivable','!=','0.0')]",
    #                                   string="Ordenes de venta")
    line_ids = fields.One2many("guazu.payment.line", "payment_id", "Detalles")
    payment_amount = fields.Monetary("Importe depositado", default=0)
    sales_amount = fields.Monetary("Importe de las ventas", compute=_compute_sales_amount, store=True)
    #discount = fields.Monetary("Aporte", required=True, default=0)
    #distributable_amount = fields.Monetary("A distribuir", compute=_compute_distributable, store=True)
    #amount_total = fields.Monetary("Importe total", compute=_amount_all, store=True)
    #tax_total = fields.Monetary("Impuesto total", compute=_amount_all, store=True)
    #net_total = fields.Monetary("Neto total", compute=_amount_all, store=True)
    note = fields.Text("Notas")
    state = fields.Selection([('draft', 'Depósito'), ('done', 'Liquidado'), ('cancel','Cancelado')],
                             default='draft', string="Estado")
    trans_nro= fields.Char("Cheque/Transacción")
    onat = fields.Monetary("% ONAT", default=0)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.sale_order_id = []

    @api.multi
    def unlink(self):
        for payment in self:
            if payment.state not in ('draft', ):
                raise UserError(_('No puede borrar un cobro que no esté en estado borrador'))
        return super(Payment, self).unlink()

    @api.one
    def case_done(self):
        if self.payment_amount <= 0:
            raise UserError(_("El importe depositado debe ser mayor que 0"))

        if self.payment_amount != self.sales_amount:
            raise UserError(_("El importe depositado debe ser igual al Importe de las ventas"))
        # if self.discount > self.payment_amount:
        #     raise UserError("El aporte no puede ser mayor que el importe depositado")

        total_amount = 0
        for line in self.line_ids:
            total_amount += line.amount
            if line.amount <= 0:
                raise UserError(_("El importe distribuido a "+line.employee_id.name+" debe ser mayor que 0"))
            if line.tax < 0:
                raise UserError("El impuesto de " + line.employee_id.name + " no puede ser negativo")
            if line.tax > line.amount:
                raise UserError(_("El impuesto de " + line.employee_id.name + " no puede ser mayor que el importe"))

        if total_amount != self.payment_amount:
            raise UserError(_("El importe distribuido no corresponde con el importe depositado"))

        if not self.trans_nro:
            raise UserError(_("Debe introducir el número de Cheque o Transacción"))

        if not self.onat:
            raise UserError(_("Debe introducir el % a la ONAT"))
        elif self.onat<=0:
            raise UserError(_("Valor del % a la ONAT incorrecto, debe ser mayor que 0"))

        if self.sale_order_id:
            if self.sales_amount < self.payment_amount:
                raise UserError(_("El importe depositado no se corresponde con el importe de las ventas"))

            for sale in self.sale_order_id:
                sale.write({'payment_id': self.id,'state':'pay'})
        self.write({'state': 'done'})

    @api.model
    def create(self, vals):
        result = super(Payment, self).create(vals)
        sales_obj = self.env['guazu.sale.order']
        cond = [('id', '=', vals['sale_order_id'])]
        sales = sales_obj.search(cond)
        for sale in sales:
            sale.state='register'
        return result
