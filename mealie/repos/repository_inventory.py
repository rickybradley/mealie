from pydantic import UUID4

from mealie.db.models.household.inventory import InventoryItem
from mealie.schema.household.group_inventory import InventoryItemOut, InventoryItemUpdate

from .repository_generic import HouseholdRepositoryGeneric


class RepositoryInventory(HouseholdRepositoryGeneric[InventoryItemOut, InventoryItem]):
    def update(self, item_id: UUID4, data: InventoryItemUpdate) -> InventoryItemOut:  # type: ignore
        return super().update(item_id, data)
