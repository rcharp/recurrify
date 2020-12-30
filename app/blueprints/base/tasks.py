from app.app import create_celery_app
import time
from app.extensions import db
from sqlalchemy import exists
from flask_login import current_user

celery = create_celery_app()


@celery.task()
def encrypt_string(plaintext):
    from app.blueprints.base.encryption import encrypt_string
    return encrypt_string(plaintext)


@celery.task()
def sync_product(source_id, destination_id, product_id, destination_products):
    from app.blueprints.shopify.functions import sync_or_create_product, add_source_tag
    from app.blueprints.shopify.functions import get_product_by_id
    from app.blueprints.shopify.models.product import SyncedProduct
    from app.blueprints.shopify.models.shop import Shop

    source = Shop.query.filter(Shop.shop_id == source_id).scalar()
    if source is None:
        return

    # Get the synced product for the table
    p = SyncedProduct.query.filter(SyncedProduct.source_product_id == product_id).scalar()
    if p is None:
        return

    # Get the product from the source store via its id
    product = get_product_by_id(source, product_id, return_json=True)

    # Add the source product's id to the tag in order to identify it during sync
    add_source_tag(product, product_id)

    # Create or update the product in the destination store
    destination_product_id = sync_or_create_product(destination_id, product, destination_products)

    # Update the newly created product's destination product id in the table.
    if destination_product_id is not None:
        p.destination_product_id = destination_product_id
        p.save()


@celery.task()
def update_product(destination_shop_id, destination_product_id, source_product):
    from app.blueprints.shopify.functions import update_product
    update_product(destination_shop_id, destination_product_id, source_product)


@celery.task()
def create_product(destination_shop_id, source_product):
    from app.blueprints.shopify.functions import create_product
    create_product(destination_shop_id, source_product)


@celery.task()
def delete_syncs(token, url, products):
    from app.blueprints.shopify.functions import delete_product

    for product in products:
        delete_product(token, url, product)
