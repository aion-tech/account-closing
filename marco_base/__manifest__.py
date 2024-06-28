{
    "name": "marco_base",
    "summary": "",
    "description": "",
    "author": "MARCO S.p.A.",
    "website": "https://www.marco.it/",
    "category": "Uncategorized",
    "version": "16.0.1.0.0",
    "depends": [
        "base",
       # "l10n_generic_auto_transfer_demo",
       # "l10n_generic_coa",
        "account_accountant",
        "l10n_it_marco_extra",
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
        "l10n_it_fatturapa_in_rc",
        "l10n_it_fatturapa_out",
        "l10n_it_fatturapa_out_di",
        "l10n_it_fatturapa_out_rc",
        "l10n_it_fatturapa_out_sp",
        "l10n_it_fatturapa_out_stamp",
        "l10n_it_fatturapa_out_wt",
        "l10n_it_fatturapa_pec",
        "l10n_it_fatturapa_sale",
        "l10n_it_financial_statements_report",
        "l10n_it_fiscal_document_type",
        "l10n_it_fiscal_payment_term",
        "l10n_it_intrastat",
        "l10n_it_intrastat_statement",
        "l10n_it_ipa",
        "l10n_it_payment_reason",
        "l10n_it_rea",
        "l10n_it_reverse_charge",
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
        "marco_maintenance",
        "microsoft_account",
        "microsoft_calendar",
        "microsoft_outlook",
        "partner_firstname",
        "report_xml",
        "sale_project_stock",
        "websocket_refresh",
        "marco_importer",
        "mrp_subcontracting",
        "mrp_multi_level",
    ],
    "data": [
        # security/ir.model.access.csv,
        # "views/views.xml",
    ],
    "post_init_hook":"marco_post_init_hook",
    "installable": True,
}
