# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Italy - Accounting - MARCO S.p.A.',
    'version': '0.6',
    'depends': [
        'account',
        "account_accountant",
        'base_iban',
        'base_vat',
        "l10n_it_reverse_charge",
        "l10n_it_fatturapa_in_rc",
        "l10n_it_fatturapa_out_rc",
        "l10n_it_fiscal_document_type",
        "l10n_it_abicab",
        "l10n_it_account_stamp",
        "l10n_it_account_tax_kind",
        "l10n_it_appointment_code",
        "l10n_it_central_journal_reportlab",
        "l10n_it_declaration_of_intent",
        "l10n_it_fatturapa",
        "l10n_it_fatturapa_export_zip",
        "l10n_it_fatturapa_import_zip",
        "l10n_it_fatturapa_in",
        "l10n_it_fatturapa_in_purchase",
        "l10n_it_fatturapa_out",
        "l10n_it_fatturapa_out_di",
        "l10n_it_fatturapa_out_sp",
        "l10n_it_fatturapa_out_stamp",
        "l10n_it_fatturapa_out_wt",
        "l10n_it_fatturapa_pec",
        "l10n_it_fatturapa_sale",
        "l10n_it_financial_statements_report",
        
        "l10n_it_fiscal_payment_term",
        "l10n_it_intrastat",
        "l10n_it_intrastat_statement",
        "l10n_it_ipa",
        "l10n_it_payment_reason",
        "l10n_it_rea",
        
        "l10n_it_riba",
        "l10n_it_sdi_channel",
        "l10n_it_split_payment",
        "l10n_it_vat_payability",
        "l10n_it_vat_registries",
        "l10n_it_vat_registries_split_payment",
        "l10n_it_vat_statement_communication",
        "l10n_it_vat_statement_split_payment",
        "l10n_it_website_portal_fatturapa",
        "l10n_it_website_portal_ipa",
        "l10n_it_withholding_tax",
        "l10n_it_withholding_tax_reason",
    ],
    'author': 'OpenERP Italian Community, MARCO S.p.A.',
    'description': """
Piano dei conti italiano della MARCO S.p.A. .
================================================

Italian accounting chart and localization.
    """,
    'category': 'Accounting/Localizations/Account Charts',
    'website': 'http://www.odoo.com/',
    'data': [
        "data/marco_partner_company.xml",
        'data/account_account_tag.xml',
        'data/account_chart_template.xml',
        'data/account_account_template.xml',
        'data/account_account_template_manual.xml',
        'data/account_account_group.xml',    
        'data/account_chart_template_accounts.xml',     
        'data/account_tax_registry.xml',
        'data/account_tax_group.xml',
        'data/account_tax_template.xml',
        'data/account_chart_template_data.xml',
        
    ],
    'demo': [
       # 'demo/demo_company.xml',
    ],
    'license': 'LGPL-3',
}
