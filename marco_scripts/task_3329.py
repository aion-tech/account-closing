# crea folder agli equipments
for doc in self.env["maintenance.equipment"].search([]):
    doc._get_document_folder()

# assegna sequenza alle requests
reqs = self.env["maintenance.request"].search([], order="create_date asc")
for r in reqs:
    next_sequence = self.env["ir.sequence"].sudo().next_by_code("maintenance.sequence")
    r.name_sequence = next_sequence

self.env.cr.commit()
