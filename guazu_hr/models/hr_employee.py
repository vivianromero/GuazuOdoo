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


class Employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    is_cutter = fields.Boolean("Es cortador", default=False)
    is_artisan = fields.Boolean("Es artesano", default=False)
    is_authorized = fields.Boolean("Tiene dispensa", default=False)




