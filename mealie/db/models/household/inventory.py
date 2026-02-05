from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models.recipe.ingredient import IngredientFoodModel, IngredientUnitModel

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from ..group import Group
    from ..users import User
    from .household import Household


class InventoryItem(SqlAlchemyBase, BaseMixins):
    __tablename__ = "inventory_items"

    # Ids
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    group_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("groups.id"), index=True, nullable=False)
    household_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("households.id"), index=True, nullable=False)
    user_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("users.id"))

    # Relationships
    group: Mapped["Group"] = orm.relationship("Group", foreign_keys=[group_id])
    household: Mapped["Household"] = orm.relationship("Household", foreign_keys=[household_id])
    user: Mapped[Optional["User"]] = orm.relationship("User", foreign_keys=[user_id])

    # Item Data
    food_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("ingredient_foods.id"), nullable=False)
    food: Mapped[IngredientFoodModel] = orm.relationship(IngredientFoodModel, uselist=False)

    quantity: Mapped[float] = mapped_column(Float, default=1, nullable=False)

    unit_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("ingredient_units.id"))
    unit: Mapped[IngredientUnitModel | None] = orm.relationship(IngredientUnitModel, uselist=False)

    # MVP: location hardcoded to 'freezer'
    location: Mapped[str] = mapped_column(String, default="freezer", nullable=False)

    # Optional fields
    note: Mapped[str | None] = mapped_column(String)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
