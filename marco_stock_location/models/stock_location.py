# marco_stock_location/models/stock_location.py

from odoo import models, api
import requests
from urllib.parse import quote
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class Location(models.Model):
    _inherit = 'stock.location'


    @api.depends('name', 'location_id.complete_name', 'usage')
    def _compute_complete_name(self):
        for location in self:
            if location.location_id:
                location.complete_name = '%s/%s' % (location.location_id.complete_name, location.name)
            else:
                location.complete_name = location.name

    def print_locations_label_via_api(self):
        base_url = "http://labels.marco.it/Integration/locationWMS/Execute"
        
        for record in self:
            # Ensure the barcode is set and not empty
            if record.barcode:
                # Extract the barcode and ignore the (92) part
                barcode = record.barcode
                # Remove the (92) prefix
                barcode_body = barcode[2:]
                # Split by hyphen
                parts = barcode_body.split('-')

                if len(parts) != 6:
                    _logger.warning(f"Invalid barcode format for location '{record.name}' (ID: {record.id}): {barcode}")
                    raise UserError(f"Invalid barcode format for location '{record.name}' (ID: {record.id}). Expected format: M3-A1-A-01-A-P1")
            
                # Construct the parameters
                title = "LIVELLO " + parts[-2]  # Text between the last and penultimate hyphen
                subtitle = barcode_body  # Full barcode without (92)
                par1label = "CORSIA"
                par1value = parts[2]  # Between the second and third hyphen
                par2label = "CAMPATA"
                par2value = parts[3]  # Between the third and fourth hyphen
                par3label = "POSIZIONE"
                par3value = parts[-1]  # After the last hyphen
                
                # Manually construct the query parameters
                params = {
                    'barcode':barcode,
                    'title': title,
                    'subtitle': subtitle,
                    'par1label': par1label,
                    'par1value': par1value,
                    'par2label': par2label,
                    'par2value': par2value,
                    'par3label': par3label,
                    'par3value': par3value,
                }
                
                # Encode the parameters manually
                query_string = '&'.join(f"{key}={quote(str(value))}" for key, value in params.items())
                
                # Construct the full URL with parameters
                url_with_params = f"{base_url}?{query_string}"
                
                try:
                    # Send the GET request
                    response = requests.get(url_with_params)
                    # Log the response using the logger
                    _logger.info(f"Request sent to {url_with_params}, response status: {response.status_code}")
                except requests.RequestException as e:
                    # Log the error using the logger
                    _logger.error(f"Error sending request for record {record.id}: {e}")
