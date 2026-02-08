<template>
  <v-container>
    <BaseDialog
      v-model="createDialog"
      :title="$t('inventory.create-new-item')"
      can-submit
      @submit="createOne"
    >
      <v-card-text>
        <InputLabelType
          v-model="newInventoryItem.food"
          v-model:item-id="foodIdModel"
          :items="allFoods"
          :label="$t('shopping-list.food')"
          :icon="globals.icons.foods"
          create
          @create="createInventoryFood"
        />
        <v-text-field
          v-model.number="newInventoryItem.quantity"
          type="number"
          :label="$t('inventory.quantity')"
          step="1"
          min="1"
          class="mt-4"
        />
        <v-select
          v-model="newInventoryItem.unitId"
          :items="availableUnits"
          :label="$t('inventory.unit')"
          item-title="name"
          item-value="id"
          clearable
          class="mt-4"
        />
      </v-card-text>
    </BaseDialog>

    <v-row>
      <v-col>
        <h1>{{ $t('inventory.inventory-page') }}</h1>
        <p>{{ $t('inventory.inventory-placeholder') }}</p>
        <v-container class="d-flex align-center justify-end px-0 pt-0 pb-4">
          <BaseButton
            create
            class="my-0"
            @click="createDialog = true"
          />
        </v-container>
        <v-expansion-panels v-model="expandedPanels">
          <v-expansion-panel>
            <v-expansion-panel-title>
              {{ $t('inventory.inventory-items') }}
            </v-expansion-panel-title>
            <v-expansion-panel-text
              v-for="item in groupedInventoryDisplayItems"
              :key="item.foodName"
            >
              <div class="d-flex justify-space-between align-center">
                <span class="d-flex align-center">{{ item.foodName }}</span>
                <div class="d-flex align-center">
                  <span class="mr-2 text-subtitle-1 d-flex align-center justify-center">{{ displayedQuantityPerFood[item.foodName] || 0 }}</span>
                  <v-select
                    v-model="selectedUnitPerFood[item.foodName]"
                    :items="item.availableUnitsForRow"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    hide-details
                    class="mr-2"
                    style="width: 115px;"
                  />
                  <v-btn
                    size="small"
                    class="mr-2"
                    variant="outlined"
                    @click="decreaseQuantity(item.foodName, selectedUnitPerFood[item.foodName])"
                  >
                    -
                  </v-btn>
                  <v-btn
                    size="small"
                    class="mr-2"
                    variant="outlined"
                    @click="increaseQuantity(item.foodName, selectedUnitPerFood[item.foodName])"
                  >
                    +
                  </v-btn>
                  <BaseButton
                    delete
                    small
                    @click="deleteGroupedItems(item.foodName)"
                  />
                </div>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { defineNuxtComponent, useNuxtApp } from "#app";
import { useAuthBackend } from "~/composables/use-auth-backend";
import InputLabelType from "~/components/global/InputLabelType.vue";
import { useFoodStore, useFoodData } from "~/composables/store";
import { useUserApi } from "~/composables/api";
import type { InventoryItemOut, InventoryItemCreate, InventoryItemUpdate } from "~/lib/api/types/household";
import type { IngredientUnit } from "~/lib/api/types/recipe";

export default defineNuxtComponent({
  name: "InventoryPage",
  components: { InputLabelType },
  setup() {
    const { $globals } = useNuxtApp();
    const api = useUserApi();
    const auth = useAuthBackend();
    const foodStore = useFoodStore();
    const foodData = useFoodData();

    const inventoryItems = ref<InventoryItemOut[]>([]);
    const createDialog = ref(false);
    const isLoading = ref(false);
    const expandedPanels = ref([0]); // Default to expanded
    const availableUnits = ref<IngredientUnit[]>([]);
    const newInventoryItem = reactive<{ food: any | null; foodId: string | null; quantity: number; unitId: string | null }>(
      {
        food: null,
        foodId: null,
        quantity: 1,
        unitId: null,
      },
    );

    const selectedUnitPerFood = reactive<Record<string, string | null>>({});

    const displayedQuantityPerFood = computed(() => {
      const quantities: Record<string, number> = {};
      groupedInventoryDisplayItems.value.forEach((item) => {
        const selectedUnitId = selectedUnitPerFood[item.foodName];
        if (selectedUnitId && item.quantitiesByUnitId[selectedUnitId]) {
          quantities[item.foodName] = item.quantitiesByUnitId[selectedUnitId];
        }
        else {
          quantities[item.foodName] = 0; // Default if no unit selected or found
        }
      });
      return quantities;
    });

    const displayedUnitNamePerFood = computed(() => {
      const unitNames: Record<string, string> = {};
      groupedInventoryDisplayItems.value.forEach((item) => {
        const selectedUnitId = selectedUnitPerFood[item.foodName];
        let selectedUnit: IngredientUnit | undefined;
        if (selectedUnitId) {
          selectedUnit = item.unitsByUnitId[selectedUnitId];
        }
        unitNames[item.foodName] = selectedUnit ? selectedUnit.name : "";
      });
      return unitNames;
    });

    const foodIdModel = computed({
      get: () => newInventoryItem.foodId || undefined,
      set: (value: string | number | undefined) => {
        newInventoryItem.foodId = (value as string) || null;
      },
    });

    const groupedInventoryDisplayItems = computed(() => {
      const grouped: Record<string, {
        unitsSummary: Record<string, { quantity: number; unitName: string | undefined }>;
        unitsByUnitId: Record<string, IngredientUnit>;
        quantitiesByUnitId: Record<string, number>;
      }> = {};

      inventoryItems.value.forEach((item) => {
        const foodName = (item.food?.name || "Unknown Food").toLowerCase(); // Normalize to lowercase
        const unitName = item.unit?.name || "unit";
        const unitId = item.unit?.id || "none";
        const unit = item.unit;

        if (!grouped[foodName]) {
          grouped[foodName] = {
            unitsSummary: {},
            unitsByUnitId: {},
            quantitiesByUnitId: {},
          };
        }

        // For unitsSummary (maintaining original 'units' string logic)
        if (!grouped[foodName].unitsSummary[unitName]) {
          grouped[foodName].unitsSummary[unitName] = {
            quantity: 0,
            unitName: item.unit?.name,
          };
        }
        grouped[foodName].unitsSummary[unitName].quantity += item.quantity || 0;

        // For new dynamic quantity display
        if (unit) {
          grouped[foodName].unitsByUnitId[unitId] = unit;
        }
        else if (unitId === "none") {
          // Add a placeholder for 'none' unit if not already present
          if (!grouped[foodName].unitsByUnitId[unitId]) {
            grouped[foodName].unitsByUnitId[unitId] = { id: "none", name: "None", unitType: "none", created: "", updated: "" } as IngredientUnit;
          }
        }

        if (!grouped[foodName].quantitiesByUnitId[unitId]) {
          grouped[foodName].quantitiesByUnitId[unitId] = 0;
        }
        grouped[foodName].quantitiesByUnitId[unitId] += item.quantity || 0;
      });

      return Object.keys(grouped)
        .sort((a, b) => a.localeCompare(b))
        .map((foodName) => {
          const foodGroup = grouped[foodName];
          return {
            foodName,
            units: Object.keys(foodGroup.unitsSummary)
              .map((unitKey) => {
                const unitData = foodGroup.unitsSummary[unitKey];
                const qty = unitData.quantity;
                const unit = unitData.unitName ? ` ${unitData.unitName}` : "";
                return `${qty}${unit}`;
              }).join(", "),
            // New additions
            quantitiesByUnitId: foodGroup.quantitiesByUnitId,
            unitsByUnitId: foodGroup.unitsByUnitId,
            availableUnitsForRow: Object.values(foodGroup.unitsByUnitId),
          };
        });
    });

    const { store: allFoods } = useFoodStore();

    // Watch for changes in groupedInventoryDisplayItems or availableUnits
    watch([groupedInventoryDisplayItems, availableUnits], () => {
      groupedInventoryDisplayItems.value.forEach((item) => {
        if (!(item.foodName in selectedUnitPerFood) && item.availableUnitsForRow.length > 0) {
          // Attempt to find "Pack" unit within the row's available units, otherwise use the first available unit in the row
          const defaultUnit = item.availableUnitsForRow.find(unit => unit.name?.toLowerCase() === "pack")
            || item.availableUnitsForRow[0];
          selectedUnitPerFood[item.foodName] = defaultUnit ? defaultUnit.id : null;
        }
      });
    }, { immediate: true }); // Initialize on first run

    async function loadInventory() {
      try {
        isLoading.value = true;
        const { data } = await api.inventory.getAll();
        if (data && data.items) {
          inventoryItems.value = data.items.sort((a, b) => {
            const nameA = a.food?.name?.toLowerCase() || "";
            return nameA.localeCompare(b.food?.name?.toLowerCase() || "");
          });
        }
      }
      catch (error) {
        console.error("Failed to load inventory:", error);
      }
      finally {
        isLoading.value = false;
      }
    }

    async function loadUnits() {
      try {
        const { data } = await api.units.getAll();
        if (data && data.items) {
          availableUnits.value = data.items;
          // Set default unit to "Pack" if available
          const packUnit = data.items.find((unit: IngredientUnit) => unit.name?.toLowerCase() === "pack");
          if (packUnit) {
            newInventoryItem.unitId = packUnit.id;
          }
        }
      }
      catch (error) {
        console.error("Failed to load units:", error);
      }
    }

    async function createInventoryFood(name: string) {
      foodData.data.name = name;
      const newFood = await foodStore.actions.createOne(foodData.data);
      if (newFood) {
        newInventoryItem.food = newFood;
        newInventoryItem.foodId = newFood.id;
      }
      foodData.reset();
    }

    async function createOne() {
      if (!newInventoryItem.foodId) {
        return;
      }

      // Ensure the user session is loaded and authenticated before attempting create
      if (auth.status.value !== "authenticated") {
        try {
          await auth.getSession();
        }
        catch (e) {
          console.error("Failed to load session before creating inventory item:", e);
        }
      }

      if (auth.status.value !== "authenticated") {
        console.error("User is not authenticated — cannot create inventory item");
        return;
      }

      try {
        const itemData: InventoryItemCreate = {
          foodId: newInventoryItem.foodId,
          quantity: newInventoryItem.quantity,
          unitId: newInventoryItem.unitId,
          location: "freezer",
          note: null,
        };

        const { data: newItem } = await api.inventory.createOne(itemData);
        if (newItem) {
          // Check if item already exists in the list (smart-merge case)
          const existingIndex = inventoryItems.value.findIndex(item => item.id === newItem.id);
          if (existingIndex >= 0) {
            // Update existing item
            inventoryItems.value[existingIndex] = newItem;
          }
          else {
            // Add new item
            inventoryItems.value.push(newItem);
          }
          newInventoryItem.food = null;
          newInventoryItem.foodId = null;
          newInventoryItem.quantity = 1;
          // Reset to default "Pack" unit if available
          const packUnit = availableUnits.value.find(unit => unit.name?.toLowerCase() === "pack");
          newInventoryItem.unitId = packUnit?.id || null;
          createDialog.value = false;
        }
      }
      catch (error) {
        console.error("Failed to create inventory item:", error);
      }
    }

    async function deleteGroupedItems(foodName: string) {
      try {
        isLoading.value = true;
        const itemsToDelete = inventoryItems.value.filter(item => item.food?.name === foodName);

        for (const item of itemsToDelete) {
          await api.inventory.deleteOne(item.id);
        }

        inventoryItems.value = inventoryItems.value.filter(item => item.food?.name !== foodName);
      }
      catch (error) {
        console.error("Failed to delete grouped inventory items:", error);
      }
      finally {
        isLoading.value = false;
      }
    }

    function increaseQuantity(foodName: string, unitId: string | null) {
      const itemToUpdateIndex = inventoryItems.value.findIndex(
        item => item.food?.name === foodName && (item.unit?.id === unitId || (unitId === "none" && !item.unit?.id)),
      );
      if (itemToUpdateIndex > -1) {
        const itemToUpdate = inventoryItems.value[itemToUpdateIndex];
        const newQuantity = (itemToUpdate.quantity || 0) + 1;

        const payload: InventoryItemUpdate = {
          id: itemToUpdate.id,
          foodId: itemToUpdate.foodId,
          quantity: newQuantity,
          unitId: itemToUpdate.unitId,
          location: itemToUpdate.location,
          note: itemToUpdate.note,
        };

        api.inventory.updateOne(itemToUpdate.id, payload)
          .then(({ data: updatedItem }) => {
            if (updatedItem) {
              inventoryItems.value.splice(itemToUpdateIndex, 1, updatedItem); // Replace old item with updated one
            }
          })
          .catch((error) => {
            console.error("Failed to update inventory item quantity:", error);
            // Optionally, revert local change if API fails
          });
      }
      else {
        console.warn(`No inventory item found for ${foodName} with unit ${unitId} to increase quantity.`);
        // Consider creating a new item if user clicks + on a non-existent item/unit combination
      }
    }

    function decreaseQuantity(foodName: string, unitId: string | null) {
      const itemToUpdateIndex = inventoryItems.value.findIndex(
        item => item.food?.name === foodName && (item.unit?.id === unitId || (unitId === "none" && !item.unit?.id)),
      );
      if (itemToUpdateIndex > -1) {
        const itemToUpdate = inventoryItems.value[itemToUpdateIndex];
        const newQuantity = Math.max(0, (itemToUpdate.quantity || 0) - 1); // Ensure quantity doesn't go below 0

        if (newQuantity === 0) {
          // If quantity becomes 0, delete the item
          api.inventory.deleteOne(itemToUpdate.id)
            .then(() => {
              inventoryItems.value.splice(itemToUpdateIndex, 1); // Remove from local state
            })
            .catch((error) => {
              console.error("Failed to delete inventory item:", error);
            });
        }
        else {
          const payload: InventoryItemUpdate = {
            id: itemToUpdate.id,
            foodId: itemToUpdate.foodId,
            quantity: newQuantity,
            unitId: itemToUpdate.unitId,
            location: itemToUpdate.location,
            note: itemToUpdate.note,
          };
          api.inventory.updateOne(itemToUpdate.id, payload)
            .then(({ data: updatedItem }) => {
              if (updatedItem) {
                inventoryItems.value.splice(itemToUpdateIndex, 1, updatedItem); // Replace old item with updated one
              }
            })
            .catch((error) => {
              console.error("Failed to update inventory item quantity:", error);
              // Optionally, revert local change if API fails
            });
        }
      }
      else {
        console.warn(`No inventory item found for ${foodName} with unit ${unitId} or quantity is already 0.`);
      }
    }

    onMounted(() => {
      loadInventory();
      loadUnits();
    });

    return {
      inventoryItems,
      createDialog,
      isLoading,
      expandedPanels,
      availableUnits,
      newInventoryItem,
      foodIdModel,
      groupedInventoryDisplayItems,
      allFoods,
      selectedUnitPerFood,
      displayedQuantityPerFood,
      displayedUnitNamePerFood,
      createInventoryFood,
      createOne,
      increaseQuantity,
      decreaseQuantity,
      deleteGroupedItems,
      globals: $globals,
    };
  },
});
</script>
