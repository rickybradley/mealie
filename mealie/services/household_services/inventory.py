import logging
from typing import cast

from pydantic import UUID4

from mealie.repos.repository_factory import AllRepositories
from mealie.schema.household.group_inventory import (
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemsCollectionOut,
    InventoryItemUpdate,
    InventoryItemUpdateBulk,
)
from mealie.schema.response.pagination import PaginationQuery

logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self, repos: AllRepositories):
        self.repos = repos
        self.inventory = repos.inventory

    def create_one(self, data: InventoryItemCreate) -> InventoryItemOut:
        """Create a single inventory item with smart-merge for existing items

        If an item with the same food_id and unit_id already exists,
        update its quantity by adding the new quantity to the existing.
        Otherwise, create a new item.
        """
        try:
            # Check for existing item with the same food_id and unit_id
            existing_items = self.inventory.multi_query({"food_id": data.food_id, "unit_id": data.unit_id}, limit=1)

            if existing_items:
                # Item exists, update its quantity
                existing_item = existing_items[0]
                new_quantity = existing_item.quantity + data.quantity
                update_data = InventoryItemUpdate(
                    id=existing_item.id,
                    food_id=existing_item.food_id,
                    quantity=new_quantity,
                    unit_id=existing_item.unit_id,
                    location=existing_item.location,
                    note=existing_item.note,
                )
                logger.info(
                    f"Item with food_id={data.food_id}, unit_id={data.unit_id} already exists. "
                    f"Updating quantity from {existing_item.quantity} to {new_quantity}"
                )
                result = cast(InventoryItemOut, self.inventory.update(existing_item.id, update_data))
                logger.info(f"Successfully updated inventory item: {result.id}")
                return result
            else:
                # Item doesn't exist, create it
                logger.info(f"Creating new inventory item with data: {data}")
                result = cast(InventoryItemOut, self.inventory.create(data))
                logger.info(f"Successfully created inventory item: {result.id}")
                return result
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}", exc_info=True)
            raise

    def create_many(self, items: list[InventoryItemCreate]) -> InventoryItemsCollectionOut:
        """Create multiple inventory items"""
        created = [self.inventory.create(item) for item in items]
        return InventoryItemsCollectionOut(created_items=created)

    def get_one(self, item_id: UUID4) -> InventoryItemOut:
        """Get a single inventory item"""
        return cast(InventoryItemOut, self.inventory.get_one(item_id))

    def get_all(
        self,
        pagination: PaginationQuery,
    ) -> tuple[list[InventoryItemOut], int]:
        """Get all inventory items with pagination"""
        page = self.inventory.page_all(pagination)
        return page.items, page.total

    def update_one(self, item_id: UUID4, data: InventoryItemUpdate) -> InventoryItemOut:
        """Update a single inventory item"""
        return cast(InventoryItemOut, self.inventory.update(item_id, data))

    def update_many(self, items: list[InventoryItemUpdateBulk]) -> InventoryItemsCollectionOut:
        """Update multiple inventory items"""
        updated = [self.inventory.update(item.id, item) for item in items]
        return InventoryItemsCollectionOut(updated_items=updated)

    def delete_one(self, item_id: UUID4) -> InventoryItemOut:
        """Delete a single inventory item"""
        return cast(InventoryItemOut, self.inventory.delete(item_id))

    def delete_many(self, item_ids: list[UUID4]) -> InventoryItemsCollectionOut:
        """Delete multiple inventory items"""
        deleted = [cast(InventoryItemOut, self.inventory.delete(item_id)) for item_id in item_ids]
        return InventoryItemsCollectionOut(deleted_items=deleted)
