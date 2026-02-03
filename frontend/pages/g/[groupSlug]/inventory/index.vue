<template>
  <v-container>
    <v-row>
      <v-col>
        <h1>Inventory Page</h1>
        <p>This is a placeholder for the inventory page.</p>
        <v-expansion-panels>
          <v-expansion-panel>
            <v-expansion-panel-title>
              Inventory Items
            </v-expansion-panel-title>
            <v-expansion-panel-text
              v-for="(item, index) in inventoryItems"
              :key="index"
            >
              {{ item }}
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
export default {
  name: "InventoryPage",
  data() {
    return {
      inventoryItems: ["steak", "chicken breasts", "pork tenderloin"],
    };
  },
};
</script>
