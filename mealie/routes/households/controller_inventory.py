from functools import cached_property

from fastapi import APIRouter, Depends, Query
from pydantic import UUID4

from mealie.routes._base.base_controllers import BaseCrudController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.schema.household.group_inventory import (
    InventoryItemCreate,
    InventoryItemOut,
    InventoryItemPagination,
    InventoryItemsCollectionOut,
    InventoryItemUpdate,
    InventoryItemUpdateBulk,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import SuccessResponse
from mealie.services.household_services.inventory import InventoryService

router = APIRouter(prefix="/households/inventory/items", tags=["Households: Inventory"])


@controller(router)
class InventoryController(BaseCrudController):
    @cached_property
    def service(self):
        return InventoryService(self.repos)

    @cached_property
    def repo(self):
        return self.repos.inventory

    @cached_property
    def mixins(self):
        return HttpRepo[InventoryItemCreate, InventoryItemOut, InventoryItemCreate](
            self.repo,
            self.logger,
        )

    @router.get("", response_model=InventoryItemPagination)
    def get_all(self, q: PaginationQuery = Depends()):
        response = self.repo.page_all(pagination=q, override=InventoryItemOut)
        response.set_pagination_guides(router.url_path_for("get_all"), q.model_dump())
        return response

    @router.post("", response_model=InventoryItemOut, status_code=201)
    def create_one(self, data: InventoryItemCreate):
        return self.service.create_one(data)

    @router.post("/create-bulk", response_model=InventoryItemsCollectionOut, status_code=201)
    def create_many(self, data: list[InventoryItemCreate]):
        return self.service.create_many(data)

    @router.get("/{item_id}", response_model=InventoryItemOut)
    def get_one(self, item_id: UUID4):
        return self.mixins.get_one(item_id)

    @router.put("/{item_id}", response_model=InventoryItemOut)
    def update_one(self, item_id: UUID4, data: InventoryItemUpdate):
        return self.service.update_one(item_id, data)

    @router.put("", response_model=InventoryItemsCollectionOut)
    def update_many(self, data: list[InventoryItemUpdateBulk]):
        return self.service.update_many(data)

    @router.delete("/{item_id}", response_model=SuccessResponse)
    def delete_one(self, item_id: UUID4):
        self.service.delete_one(item_id)
        return SuccessResponse.respond()

    @router.delete("", response_model=SuccessResponse)
    def delete_many(self, ids: list[UUID4] = Query(None)):
        self.service.delete_many(ids)
        return SuccessResponse.respond()
