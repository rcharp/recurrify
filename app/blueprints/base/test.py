
def test():
    from app.blueprints.base.dns.heroku import create_subdomain
    from app.blueprints.base.functions import print_traceback

    try:
        print("Creating subdomain...")
        return create_subdomain('test')
    except Exception as e:
        print_traceback(e)
        return None