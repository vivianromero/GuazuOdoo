# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError


class StockMoveDone(models.TransientModel):
    """
    This wizard will end the all the selected draft stock moves
    """

    _name = "guazu.stock.move.done"
    _description = "Ends the selected stock moves"

    @api.multi
    def stock_move_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['guazu.stock.move'].browse(active_ids):
            if not record.state in ['draft', 'wait']:
                raise UserError(_("Los movimientos seleccionados no pueden ser terminados porque no están en estado 'borrador'."))
            record.case_done()
        return {'type': 'ir.actions.act_window_close'}