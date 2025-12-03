import random
from typing import List, Optional, Dict

from . import schemas

# -------------------------------------------------------------------
# Simple in-memory "database" to avoid DynamoDB / IAM permissions
# -------------------------------------------------------------------
# Key: int product_id
# Value: schemas.Product
_PRODUCTS: Dict[int, schemas.Product] = {}


def _generate_product_id() -> int:
    """
    Generate a simple integer ID for products.
    Ensures it is unique within this process.
    NOTE: Data is in-memory only and will reset when the server restarts.
    """
    while True:
        product_id = random.randint(1, 10**9)
        if product_id not in _PRODUCTS:
            return product_id


def create_product(item: schemas.ProductCreate) -> schemas.Product:
    """
    Create a product and store it in the in-memory dict.
    """
    product_id = _generate_product_id()
    product = schemas.Product(
        id=product_id,
        name=item.name,
        category=item.category,
        description=item.description,
    )
    _PRODUCTS[product_id] = product
    return product


def list_products() -> List[schemas.Product]:
    """
    Return all products from the in-memory store.
    """
    return list(_PRODUCTS.values())


def get_product(product_id: int) -> Optional[schemas.Product]:
    """
    Get a single product by ID.
    """
    return _PRODUCTS.get(product_id)


def update_product(
    product_id: int,
    data: schemas.ProductUpdate,
) -> Optional[schemas.Product]:
    """
    Update an existing product. Returns the updated product,
    or None if the product does not exist.
    """
    current = _PRODUCTS.get(product_id)
    if not current:
        return None

    # Merge current data with update
    new_data = current.dict()
    update_dict = data.dict(exclude_unset=True)
    new_data.update(update_dict)

    updated = schemas.Product(**new_data)
    _PRODUCTS[product_id] = updated
    return updated


def delete_product(product_id: int) -> bool:
    """
    Delete a product by ID. Returns True if deleted, False if not found.
    """
    if product_id in _PRODUCTS:
        del _PRODUCTS[product_id]
        return True
    return False
