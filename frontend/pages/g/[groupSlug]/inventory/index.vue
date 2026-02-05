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
          v-model:item-id="newInventoryItem.foodId"
          :items="allFoods"
          :label="$t('shopping-list.food')"
          :icon="globals.icons.foods"
          create
          @create="createInventoryFood"
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
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              {{ $t('inventory.inventory-items') }} ({{ inventoryItems.length }})
            </v-expansion-panel-title>
            <v-expansion-panel-text
              v-for="item in inventoryItems"
              :key="item.id"
            >
              <div class="d-flex justify-space-between align-center">
                <span>{{ item.food?.name }} - Qty: {{ item.quantity }}</span>
                <BaseButton
                  delete
                  small
                  @click="deleteItem(item.id)"
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
import { ref, reactive, onMounted } from "vue";
import { defineNuxtComponent, useNuxtApp } from "#app";
import { useAuthBackend } from "~/composables/use-auth-backend";
import InputLabelType from "~/components/global/InputLabelType.vue";
import { useFoodStore, useFoodData } from "~/composables/store";
import { useUserApi } from "~/composables/api";
import type { InventoryItemOut, InventoryItemCreate } from "~/lib/api/types/household";

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
    const newInventoryItem = reactive<{ food: any | null; foodId: string | null }>(
      {
        food: null,
        foodId: null,
      },
    );

    const { store: allFoods } = useFoodStore();

    async function loadInventory() {
      try {
        isLoading.value = true;
        const { data } = await api.inventory.getAll();
        if (data && data.items) {
          inventoryItems.value = data.items;
        }
      }
      catch (error) {
        console.error("Failed to load inventory:", error);
      }
      finally {
        isLoading.value = false;
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
          food_id: newInventoryItem.foodId,
          quantity: 1.0,
          unit_id: null,
          location: "freezer",
          note: null,
        };

        const { data: newItem } = await api.inventory.createOne(itemData);
        if (newItem) {
          inventoryItems.value.push(newItem);
          newInventoryItem.food = null;
          newInventoryItem.foodId = null;
          createDialog.value = false;
        }
      }
      catch (error) {
        console.error("Failed to create inventory item:", error);
      }
    }

    async function deleteItem(itemId: string) {
      try {
        await api.inventory.deleteOne(itemId);
        inventoryItems.value = inventoryItems.value.filter(item => item.id !== itemId);
      }
      catch (error) {
        console.error("Failed to delete inventory item:", error);
      }
    }

    onMounted(() => {
      loadInventory();
    });

    return {
      inventoryItems,
      createDialog,
      isLoading,
      newInventoryItem,
      allFoods,
      createInventoryFood,
      createOne,
      deleteItem,
      globals: $globals,
    };
  },
});
</script>
