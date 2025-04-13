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

from odoo import models, _, fields, api, exceptions


class MrpOrder(models.Model):
    _name = "guazu.mrp.order"
    _order = 'production_date desc, id desc'

    @api.one
    @api.depends('line_ids')
    def _compute_total_amount(self):
        self.total_amount = 0
        self.total_quantity = 0
        for line in self.line_ids:
            self.total_amount += line.price * line.quantity
            self.total_quantity += line.quantity

    name = fields.Char('Consecutivo', size=300, required=True, default="/")
    company_id = fields.Many2one('res.company', 'Compañía', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('guazu.mrp.order'))
    workshop_id = fields.Many2one("guazu.mrp.workshop", "Área de Producción", index=True, ondelete="restrict", required=True)
    department_id = fields.Many2one("hr.department", "Departamento", related="workshop_id.department_id", required=True)
    production_date = fields.Date(string="Fecha", index=True, required=True, copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one("res.currency", string="Moneda", related="company_id.currency_id", readonly=True,
                                  required=True)
    line_ids = fields.One2many("guazu.mrp.order.line", "order_id", "Detalles")
    total_quantity = fields.Float("Cantidad total", compute=_compute_total_amount, store=True)
    total_amount = fields.Float("Costo total", compute=_compute_total_amount, store=True)
    note = fields.Text("Notas")
    state = fields.Selection([('draft', 'Borrador'), ('done', 'Terminada'), ('cancel', 'Cancelada')],
                             default='draft', string="Estado")

    _sql_constraints = [('name', 'unique (name)', "El nombre debe ser único.")]

    @api.one
    def case_done(self):
        self.write({'state': 'done'})

    @api.one
    def case_cancel(self):
        self.write({'state': 'cancel'})

    @api.onchange('workshop_id')
    def onchange_workshop_id(self):
        self.line_ids = []

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') == '/'):
            seq_obj_name = 'guazu.mrp.order'
            vals['name'] = self.env['ir.sequence'].get(seq_obj_name)
        return super(MrpOrder, self).create(vals)

    @api.one
    def unlink(self):
        if self.state not in ('draft',):
            raise exceptions.Warning(_('Sólo se pueden eliminar órdenes en estado borrador'))

        super(MrpOrder, self).unlink()







