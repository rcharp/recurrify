import os
import heroku3
from flask import current_app
from requests.exceptions import HTTPError


def create_subdomain(subdomain):
    from app.blueprints.base.functions import print_traceback
    server_name = '.' + current_app.config.get('SERVER_NAME')

    try:
        heroku_conn = heroku3.from_key(current_app.config.get('HEROKU_TOKEN'))
        app = heroku_conn.apps()['recurrify']

        # See if the domain exists already. If so, then just create the DNS
        try:
            d = app.get_domain(subdomain + server_name)
            if d is not None:
                try:
                    dns = d.cname

                    # Create the DNS in CloudFlare
                    from app.blueprints.base.dns.cloudflare import create_dns
                    return create_dns(subdomain, dns)
                except Exception as e:
                    print_traceback(e)
                    pass
        except HTTPError as h:
            if h.response.status_code == 404: # The domain doesn't exist, so continute to create it
                print(h)
                print("Domain doesn't exist.")
                pass

        # If the domain doesn't exist, then go ahead and create it
        try:
            d = app.add_domain(subdomain + server_name)
            if d is not None:
                try:
                    dns = d.cname

                    # Create the DNS in CloudFlare
                    from app.blueprints.base.dns.cloudflare import create_dns
                    return create_dns(subdomain, dns)
                except Exception as e:
                    print_traceback(e)
                    pass
        except HTTPError as h:
            if h.response.status_code == 422: # The domain already exists, which should've been handled above
                print(h)
                print("Domain already exists.")
                
                try:
                    d = app.get_domain(subdomain + server_name)
                    dns = d.cname

                    # Create the DNS in CloudFlare
                    from app.blueprints.base.dns.cloudflare import create_dns
                    return create_dns(subdomain, dns)
                except Exception as e:
                    print_traceback(e)
                    pass

        return False
    except Exception as e:
        print_traceback(e)
        return False