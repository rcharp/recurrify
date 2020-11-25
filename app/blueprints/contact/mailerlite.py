import requests, json
from flask import current_app


def create_subscriber(email):
    url = "https://base.mailerlite.com/base/v2/groups/94534374/subscribers"

    data = {
        'email': email,
    }

    payload = json.dumps(data)

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)


def get_groups():
    url = "https://base.mailerlite.com/base/v2/groups"

    headers = {
        'content-type': "application/json",
        'x-mailerlite-apikey': current_app.config.get('MAILERLITE_API_KEY')
    }

    response = requests.request("GET", url, headers=headers)

    print(response.text)
