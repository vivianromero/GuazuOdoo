# -*- coding: utf-8 -*-
{
    'name': 'Producción',
    'version': '0.1',
    'category': 'Guazu',
    "sequence": 2,
    'complexity': "easy",
    'description': """

    """,
    'author': "Yerandy Reyes & Vivian Romero",
    'website': '',
    'depends': ["guazu_stock", "guazu_hr"],
    'init_xml': [],
    'data': [
        "security/mrp_security.xml",
        "security/ir.model.access.csv",
        "view/menu.xml",
        "view/workshop_view.xml",
        "view/activity_view.xml",
        "view/order_view.xml",
        "report/mrp_payroll_templates.xml",
        "report/mrp_reports.xml",
        "report/mrp_analysis.xml",
        "data/mrp_order_sequence.xml",
        #"data/workshop_data.xml",
        #"data/activity_cut_data.xml",
        #"data/activity_finnish_data.xml",
        "wizard/mrp_payroll_wizard_view.xml",
        "wizard/mrp_order_done_wizard_view.xml"
    ],
    'demo_xml': [],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
