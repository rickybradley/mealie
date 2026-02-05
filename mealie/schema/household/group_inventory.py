from __future__ import annotations

from datetime import datetime

from pydantic import UUID4, ConfigDict
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.interfaces import LoaderOption

from mealie.db.models.household import InventoryItem
from mealie.db.models.recipe import IngredientFoodModel
from mealie.schema._mealie import MealieModel
from mealie.schema._mealie.mealie_model import UpdatedAtField
from mealie.schema.recipe.recipe_ingredient import IngredientFood, IngredientUnit
from mealie.schema.response.pagination import PaginationBase


class InventoryItemBase(MealieModel):
    """Base model for inventory item data"""

    food_id: UUID4
    quantity: float = 1
    unit_id: UUID4 | None = None
    location: str = "freezer"
    note: str | None = None


class InventoryItemCreate(InventoryItemBase):
    """Create a new inventory item"""

    id: UUID4 | None = None
    """The unique id of the item to create. If not supplied, one will be generated."""


class InventoryItemUpdate(InventoryItemBase):
    """Update an existing inventory item"""

    id: UUID4


class InventoryItemUpdateBulk(InventoryItemUpdate):
    """Bulk update model (includes id)"""

    pass


class InventoryItemOut(InventoryItemBase):
    """Full inventory item output model"""

    id: UUID4
    group_id: UUID4
    household_id: UUID4
    user_id: UUID4 | None = None

    food: IngredientFood | None = None
    unit: IngredientUnit | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = UpdatedAtField(None)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            selectinload(InventoryItem.food).joinedload(IngredientFoodModel.extras),
            selectinload(InventoryItem.food).joinedload(IngredientFoodModel.label),
            joinedload(InventoryItem.unit),
        ]


class InventoryItemPagination(PaginationBase):
    """Paginated inventory items"""

    items: list[InventoryItemOut]


class InventoryItemsCollectionOut(MealieModel):
    """Container for bulk inventory item changes"""

    created_items: list[InventoryItemOut] = []
    updated_items: list[InventoryItemOut] = []
    deleted_items: list[InventoryItemOut] = []
