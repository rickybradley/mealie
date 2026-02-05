import pytest
from pydantic import UUID4

from mealie.schema.household.group_inventory import InventoryItemCreate, InventoryItemOut
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


def create_inventory_item(group_id: UUID4, household_id: UUID4, food_id: UUID4) -> InventoryItemCreate:
    return InventoryItemCreate(
        food_id=food_id,
        quantity=1.0,
        unit_id=None,
        location="freezer",
        note=random_string(10),
    )


@pytest.fixture(scope="function")
def inventory_items(unique_user: TestUser) -> list[InventoryItemOut]:
    """Create multiple inventory items for testing"""
    database = unique_user.repos
    foods = database.ingredient_foods.get_all(limit=3)
    models: list[InventoryItemOut] = []

    if not foods:
        pytest.skip("No ingredient foods available for testing")

    for food in foods:
        item = InventoryItemCreate(
            food_id=food.id,
            quantity=1.0,
            unit_id=None,
            location="freezer",
            note=random_string(10),
        )
        model = database.inventory.create(item)
        models.append(model)

    yield models

    for model in models:
        try:
            database.inventory.delete(model.id)
        except Exception:  # Entry deleted in test
            pass


@pytest.fixture(scope="function")
def inventory_item(unique_user: TestUser) -> InventoryItemOut:
    """Create a single inventory item for testing"""
    database = unique_user.repos
    foods = database.ingredient_foods.get_all(limit=1)

    if not foods:
        pytest.skip("No ingredient foods available for testing")

    item = InventoryItemCreate(
        food_id=foods[0].id,
        quantity=1.0,
        unit_id=None,
        location="freezer",
        note=random_string(10),
    )
    model = database.inventory.create(item)

    yield model

    try:
        database.inventory.delete(model.id)
    except Exception:  # Entry deleted in test
        pass
