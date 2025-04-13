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

from odoo import models, _, fields, api
from datetime import datetime, timedelta, date
import calendar
from odoo.exceptions import except_orm, Warning, RedirectWarning
from lxml import etree


class Workshop(models.Model):
    _name = "guazu.mrp.workshop"
    _inherits = {'guazu.stock.location': 'location_id'}

    code = fields.Char(related='location_id.code', string='Código', required=True)
    name = fields.Char(related='location_id.name', string='Nombre', required=True)
    location_id = fields.Many2one(
        'guazu.stock.location', 'Ubicación',
        auto_join=True, index=True, ondelete="cascade", required=True)
    department_id = fields.Many2one('hr.department', 'Departamento',
         index=True, ondelete="cascade", required=False)
    @api.model
    def create(self, vals):
        location = self.env["guazu.stock.location"].search([('type', '=', 'production'),
                                                            ('name', '=', vals.get('name')),
                                                            ('code', '=', vals.get('code'))
                                                            ])
        if not location:
            #create the location if not exists
            vals.update({'type': 'production'})
            location = self.env["guazu.stock.location"].create(vals)


        vals.update({'location_id': location.id})

        return super(Workshop, self).create(vals)