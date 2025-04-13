# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class MrpOrderDone(models.TransientModel):
    """
    This wizard will end the all the selected draft mrp orders
    """

    _name = "guazu.mrp.order.done"
    _description = "Ends the selected mrp orders"

    @api.multi
    def mrp_order_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['guazu.mrp.order'].browse(active_ids):
            if record.state != 'draft':
                raise UserError(_("Las órdenes seleccionadas no pueden ser terminadas porque no están en estado 'borrador'."))
            record.case_done()
        return {'type': 'ir.actions.act_window_close'}