import json
import requests
from flask import current_app


def create_godaddy_subdomain(subdomain, test=False):
    try:
        # Get the GoDaddy keys
        api_key = current_app.config.get('GODADDY_TEST_API_KEY') if test else current_app.config.get('GODADDY_API_KEY')
        api_secret = current_app.config.get('GODADDY_TEST_SECRET_KEY') if test else current_app.config.get('GODADDY_SECRET_KEY')

        # Get the URL
        # url = 'https://api.godaddy.com/v1/domains/' + current_app.config.get('DOMAIN') + '/records'
        url = 'https://base.godaddy.com/v1/domains/getmydomain.io/records'

        headers = {
            "Authorization": "sso-key " + api_key + ":" + api_secret,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        body = json.dumps([{'type': 'A', 'name': subdomain, 'data': current_app.config.get('IP_ADDRESS'), 'ttl': 3600}])

        r = requests.patch(url, headers=headers, data=body)

        if r.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return None
