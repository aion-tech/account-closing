from freezegun import freeze_time

# crea folder agli equipments
for doc in self.env["maintenance.equipment"].search([]):
    doc._get_document_folder()

# assegna sequenza alle requests
reqs = self.env["maintenance.request"].search([], order="create_date asc")
prev_request_date_month = False
sequence = self.env.ref("marco_maintenance.marco_maintenance_request_sequence")
for r in reqs:
    with freeze_time(r.create_date):
        if prev_request_date_month != r.create_date.month:
            sequence.number_next_actual = 1

        next_sequence = (
            self.env["ir.sequence"].sudo().next_by_code("maintenance.sequence")
        )
        r.name_sequence = next_sequence
        prev_request_date_month = r.create_date.month

self.env.cr.commit()
