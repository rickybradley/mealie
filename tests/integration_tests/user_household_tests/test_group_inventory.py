import pytest
from fastapi.testclient import TestClient

from mealie.schema.household.group_inventory import InventoryItemCreate
from tests import utils
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


def test_inventory_item_create_one(api_client: TestClient, unique_user: TestUser) -> None:
    """Test creating a single inventory item"""
    # Get a food first
    foods = unique_user.repos.ingredient_foods.get_all(limit=1)
    if not foods:
        pytest.skip("No ingredient foods available for testing")

    item_data = {
        "food_id": str(foods[0].id),
        "quantity": 1.0,
        "unit_id": None,
        "location": "freezer",
        "note": random_string(10),
    }

    response = api_client.post(
        api_routes.households_inventory_items,
        json=item_data,
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 201)
    assert as_json["foodId"] == str(foods[0].id)
    assert as_json["quantity"] == 1.0
    assert as_json["location"] == "freezer"

    # Verify item is gettable
    item_id = as_json["id"]
    response = api_client.get(
        api_routes.households_inventory_item_id(item_id),
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 200)
    assert as_json["id"] == item_id


def test_inventory_item_create_many(api_client: TestClient, unique_user: TestUser) -> None:
    """Test creating multiple inventory items"""
    # Get foods
    foods = unique_user.repos.ingredient_foods.get_all(limit=3)
    if len(foods) < 3:
        pytest.skip("Not enough ingredient foods available for testing")

    items_data = [
        {
            "food_id": str(food.id),
            "quantity": 1.0,
            "unit_id": None,
            "location": "freezer",
            "note": random_string(10),
        }
        for food in foods
    ]

    response = api_client.post(
        api_routes.households_inventory_items_create_bulk,
        json=items_data,
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 201)
    assert len(as_json["createdItems"]) == 3
    assert len(as_json["updatedItems"]) == 0
    assert len(as_json["deletedItems"]) == 0


def test_inventory_item_get_all(api_client: TestClient, unique_user: TestUser) -> None:
    """Test listing all inventory items with pagination"""
    # Create some items
    foods = unique_user.repos.ingredient_foods.get_all(limit=3)
    if len(foods) < 3:
        pytest.skip("Not enough ingredient foods available for testing")

    for food in foods:
        unique_user.repos.inventory.create(
            InventoryItemCreate(
                food_id=food.id,
                quantity=1.0,
                unit_id=None,
                location="freezer",
                note=random_string(10),
            )
        )

    # Get all items
    response = api_client.get(
        api_routes.households_inventory_items,
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 200)
    assert as_json["total"] >= 3
    assert len(as_json["items"]) >= 3


def test_inventory_item_update_one(api_client: TestClient, unique_user: TestUser) -> None:
    """Test updating a single inventory item"""
    # Create an item
    foods = unique_user.repos.ingredient_foods.get_all(limit=1)
    if not foods:
        pytest.skip("No ingredient foods available for testing")

    item = unique_user.repos.inventory.create(
        InventoryItemCreate(
            food_id=foods[0].id,
            quantity=1.0,
            unit_id=None,
            location="freezer",
            note="original note",
        )
    )

    # Update the item
    update_data = {
        "id": str(item.id),
        "food_id": str(item.food_id),
        "quantity": 5.0,
        "unit_id": None,
        "location": "freezer",
        "note": "updated note",
    }

    response = api_client.put(
        api_routes.households_inventory_item_id(item.id),
        json=update_data,
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 200)
    assert as_json["quantity"] == 5.0
    assert as_json["note"] == "updated note"


def test_inventory_item_update_many(api_client: TestClient, unique_user: TestUser) -> None:
    """Test bulk updating inventory items"""
    # Create some items
    foods = unique_user.repos.ingredient_foods.get_all(limit=2)
    if len(foods) < 2:
        pytest.skip("Not enough ingredient foods available for testing")

    items = []
    for food in foods:
        item = unique_user.repos.inventory.create(
            InventoryItemCreate(
                food_id=food.id,
                quantity=1.0,
                unit_id=None,
                location="freezer",
                note=random_string(10),
            )
        )
        items.append(item)

    # Bulk update
    update_data = [
        {
            "id": str(items[0].id),
            "food_id": str(items[0].food_id),
            "quantity": 10.0,
            "unit_id": None,
            "location": "freezer",
            "note": "updated 1",
        },
        {
            "id": str(items[1].id),
            "food_id": str(items[1].food_id),
            "quantity": 20.0,
            "unit_id": None,
            "location": "freezer",
            "note": "updated 2",
        },
    ]

    response = api_client.put(
        api_routes.households_inventory_items,
        json=update_data,
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 200)
    assert len(as_json["updatedItems"]) == 2


def test_inventory_item_delete_one(api_client: TestClient, unique_user: TestUser) -> None:
    """Test deleting a single inventory item"""
    # Create an item
    foods = unique_user.repos.ingredient_foods.get_all(limit=1)
    if not foods:
        pytest.skip("No ingredient foods available for testing")

    item = unique_user.repos.inventory.create(
        InventoryItemCreate(
            food_id=foods[0].id,
            quantity=1.0,
            unit_id=None,
            location="freezer",
            note=random_string(10),
        )
    )

    # Delete the item
    response = api_client.delete(
        api_routes.households_inventory_item_id(item.id),
        headers=unique_user.token,
    )
    utils.assert_deserialize(response, 200)

    # Verify deletion
    response = api_client.get(
        api_routes.households_inventory_item_id(item.id),
        headers=unique_user.token,
    )
    assert response.status_code == 404


def test_inventory_item_delete_many(api_client: TestClient, unique_user: TestUser) -> None:
    """Test bulk deleting inventory items"""
    # Create some items
    foods = unique_user.repos.ingredient_foods.get_all(limit=2)
    if len(foods) < 2:
        pytest.skip("Not enough ingredient foods available for testing")

    items = []
    for food in foods:
        item = unique_user.repos.inventory.create(
            InventoryItemCreate(
                food_id=food.id,
                quantity=1.0,
                unit_id=None,
                location="freezer",
                note=random_string(10),
            )
        )
        items.append(item)

    # Bulk delete
    item_ids = [str(item.id) for item in items]
    response = api_client.delete(
        api_routes.households_inventory_items,
        params={"ids": item_ids},
        headers=unique_user.token,
    )
    utils.assert_deserialize(response, 200)

    # Verify deletion
    for item in items:
        response = api_client.get(
            api_routes.households_inventory_item_id(item.id),
            headers=unique_user.token,
        )
        assert response.status_code == 404
