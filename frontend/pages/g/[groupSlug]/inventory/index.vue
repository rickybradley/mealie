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
              {{ $t('inventory.inventory-items') }} ({{ inventoryItems.length }})
            </v-expansion-panel-title>
            <v-expansion-panel-text
              v-for="item in groupedInventoryDisplayItems"
              :key="item.foodName"
            >
              <div class="d-flex justify-space-between align-center">
                <span>{{ item.foodName }} - Qty: {{ item.units }}</span>
                <BaseButton
                  delete
                  small
                  @click="deleteGroupedItems(item.foodName)"
                />
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
import type { InventoryItemOut, InventoryItemCreate } from "~/lib/api/types/household";
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

    const foodIdModel = computed({
      get: () => newInventoryItem.foodId || undefined,
      set: (value: string | number | undefined) => {
        newInventoryItem.foodId = (value as string) || null;
      },
    });

    const groupedInventoryDisplayItems = computed(() => {
      const grouped: Record<string, Record<string, { quantity: number; unitName: string | undefined }>> = {};

      inventoryItems.value.forEach((item) => {
        const foodName = item.food?.name || "Unknown Food";
        const unitName = item.unit?.name || "unit"; // Fallback for unit name

        if (!grouped[foodName]) {
          grouped[foodName] = {};
        }

        if (!grouped[foodName][unitName]) {
          grouped[foodName][unitName] = {
            quantity: 0,
            unitName: item.unit?.name,
          };
        }
        grouped[foodName][unitName].quantity += item.quantity || 0;
      });

      // Convert grouped object to array and sort by food name
      return Object.keys(grouped)
        .sort((a, b) => a.localeCompare(b))
        .map(foodName => ({
          foodName,
          units: Object.keys(grouped[foodName])
            .map((unitKey) => {
              const unitData = grouped[foodName][unitKey];
              const qty = unitData.quantity;
              const unit = unitData.unitName ? ` ${unitData.unitName}` : "";
              return `${qty}${unit}`;
            }).join(", "),
        }));
    });

    const { store: allFoods } = useFoodStore();

    async function loadInventory() {
      try {
        isLoading.value = true;
        const { data } = await api.inventory.getAll();
        if (data && data.items) {
          inventoryItems.value = data.items.sort((a, b) => {
            const nameA = a.food?.name?.toLowerCase() || "";
            const nameB = b.food?.name?.toLowerCase() || "";
            return nameA.localeCompare(nameB);
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
      createInventoryFood,
      createOne,
      deleteGroupedItems,
      globals: $globals,
    };
  },
});
</script>
