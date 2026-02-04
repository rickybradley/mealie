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
          :icon="$globals.icons.foods"
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
              {{ $t('inventory.inventory-items') }}
            </v-expansion-panel-title>
            <v-expansion-panel-text
              v-for="(item, index) in inventoryItems"
              :key="index"
            >
              {{ item.name }}
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { ref, reactive, computed } from "vue";
import { defineNuxtComponent, useNuxtApp } from "#app";
import { useI18n } from "#imports";
import InputLabelType from "~/components/global/InputLabelType.vue";
import { useFoodStore, useFoodData } from "~/composables/store";
import type { IngredientFood } from "~/lib/api/types/recipe";

export default defineNuxtComponent({
  name: "InventoryPage",
  components: { InputLabelType },
  setup() {
    const i18n = useI18n();
    const { $globals } = useNuxtApp();
    const foodStore = useFoodStore();
    const foodData = useFoodData();

    const inventoryItems = ref<IngredientFood[]>([]);
    const createDialog = ref(false);
    const newInventoryItem = reactive<{ food: IngredientFood | null; foodId: string | null }>(
      {
        food: null,
        foodId: null,
      },
    );

    const { store: allFoods } = useFoodStore(); // Directly use useFoodStore() for allFoods

    // The foodItems passed to InputLabelType will now be directly from the store
    // which should be a reactive array. No need for a separate computed or watch here.

    async function createInventoryFood(name: string) {
      foodData.data.name = name;
      const newFood = await foodStore.actions.createOne(foodData.data);
      if (newFood) {
        newInventoryItem.food = newFood;
        newInventoryItem.foodId = newFood.id;
        // The useFoodStore should handle refreshing its own state after creation,
        // so `allFoods` should automatically update.
      }
      foodData.reset();
    }

    function createOne() {
      if (newInventoryItem.food) {
        inventoryItems.value.push(newInventoryItem.food);
        newInventoryItem.food = null;
        newInventoryItem.foodId = null;
        createDialog.value = false;
      }
    }

    return {
      inventoryItems,
      createDialog,
      newInventoryItem,
      allFoods, // Return allFoods directly to the template
      createInventoryFood,
      createOne,
      $globals, // Make $globals available in the template
    };
  },
});
</script>
