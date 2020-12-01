class Prod:

    tags = ''

    def __init__(self, product):
        self.description = product['body_html']
        self.title = product['title']
        self.created = product['created_at']
        self.product_id = product['id']
        self.images = product['images']
        self.options = product['options']
        self.variants = product['variants']



