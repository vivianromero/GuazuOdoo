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
from odoo.addons import decimal_precision as dp


class Activity(models.Model):
    _name = "guazu.mrp.activity"

    workshop_id = fields.Many2one("guazu.mrp.workshop", "Área de Producción", index=True, ondelete="restrict", required=True)
    name = fields.Char("Nombre", required=True)
    price = fields.Float("Precio", digits=dp.get_precision('Internal Price'), required=True)

    _sql_constraints = [('workshop_id_name', 'unique (workshop_id, name)',
                         "No pueden existir dos operaciones con el mismo nombre para una misma área de producción.")]

