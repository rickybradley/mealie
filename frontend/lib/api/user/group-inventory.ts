import { BaseCRUDAPI } from "../base/base-clients";
import type {
  InventoryItemCreate,
  InventoryItemOut,
  InventoryItemUpdate,
} from "~/lib/api/types/household";

const prefix = "/api";

const routes = {
  inventoryItems: `${prefix}/households/inventory/items`,
  inventoryItemsCreateBulk: `${prefix}/households/inventory/items/create-bulk`,
  inventoryItemsId: (id: string) => `${prefix}/households/inventory/items/${id}`,
};

export class InventoryApi extends BaseCRUDAPI<InventoryItemCreate, InventoryItemOut, InventoryItemUpdate> {
  override baseRoute = routes.inventoryItems;

  override itemRoute(itemId: string): string {
    return routes.inventoryItemsId(itemId);
  }

  async createMany(items: InventoryItemCreate[]) {
    return await this.requests.post(routes.inventoryItemsCreateBulk, items);
  }

  async deleteMany(itemIds: string[]) {
    let query = "?";

    itemIds.forEach((id) => {
      query += `ids=${id}&`;
    });

    return await this.requests.delete(routes.inventoryItems + query);
  }
}
