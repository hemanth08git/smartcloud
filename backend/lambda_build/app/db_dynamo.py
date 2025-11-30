import os
import random
from typing import List, Optional

import boto3

from . import schemas

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
PRODUCTS_TABLE_NAME = os.getenv("PRODUCTS_TABLE_NAME", "SmartFoodProducts")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
products_table = dynamodb.Table(PRODUCTS_TABLE_NAME)


def _generate_product_id() -> int:
    """
    Generate a simple integer ID for products.
    Stored as a string in DynamoDB (partition key is String),
    but returned as int to match schemas.Product.id: int
    """
    return random.randint(1, 10**9)


def create_product(item: schemas.ProductCreate) -> schemas.Product:
    product_id = _generate_product_id()
    db_item = {
        "id": str(product_id),  # DynamoDB key is a string
        "name": item.name,
        "category": item.category or "",
        "description": item.description or "",
    }
    products_table.put_item(Item=db_item)
    return schemas.Product(
        id=product_id,
        name=item.name,
        category=item.category,
        description=item.description,
    )


def list_products() -> List[schemas.Product]:
    resp = products_table.scan()
    items = resp.get("Items", [])
    products: List[schemas.Product] = []

    for item in items:
        try:
            pid = int(item["id"])
        except (KeyError, ValueError, TypeError):
            # Skip malformed ids
            continue

        products.append(
            schemas.Product(
                id=pid,
                name=item.get("name", ""),
                category=item.get("category") or None,
                description=item.get("description") or None,
            )
        )

    return products


def get_product(product_id: int) -> Optional[schemas.Product]:
    resp = products_table.get_item(Key={"id": str(product_id)})
    item = resp.get("Item")
    if not item:
        return None

    return schemas.Product(
        id=int(item["id"]),
        name=item.get("name", ""),
        category=item.get("category") or None,
        description=item.get("description") or None,
    )


def update_product(
    product_id: int,
    data: schemas.ProductUpdate,
) -> Optional[schemas.Product]:
    current = get_product(product_id)
    if not current:
        return None

    # Merge current data with update
    new_data = current.dict()
    update_dict = data.dict(exclude_unset=True)
    new_data.update(update_dict)

    db_item = {
        "id": str(new_data["id"]),
        "name": new_data["name"],
        "category": new_data.get("category") or "",
        "description": new_data.get("description") or "",
    }
    products_table.put_item(Item=db_item)

    return schemas.Product(**new_data)


def delete_product(product_id: int) -> bool:
    products_table.delete_item(Key={"id": str(product_id)})
    return True
