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


class Filial(models.Model):
    _name = "guazu.payment.filial"
    description = "Filial"
    _order = 'name asc'

    name = fields.Char("Nombre", required=True)
    filial_address = fields.Char("Dirección")
    filial_reup = fields.Char("Código REUP")
    filial_nit = fields.Char("NIT")
    filial_accountCU = fields.Char("Cuenta Bancaria CUC")
    filial_accountMN = fields.Char("Cuenta Bancaria MN")
    filial_titlecheckCU = fields.Char("Cheque en CUC a título de")
    filial_titlecheckMN = fields.Char("Cheque en MN a título de")


    _sql_constraints = [('name', 'unique (name)', "El nombre debe ser único.")]