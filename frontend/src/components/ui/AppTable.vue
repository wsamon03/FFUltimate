<template>
  <div class="overflow-x-auto rounded-xl border" style="border-color: var(--color-border)">
    <table class="min-w-full text-sm">
      <thead style="background: var(--color-card)">
        <slot name="head" />
      </thead>
      <tbody style="background: var(--color-bg)">
        <slot />
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
// Intentionally empty — purely structural
</script>

<style>
/* Applied globally so slotted elements pick these up */
table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

table td {
  padding: 0.75rem 1rem;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

table tbody tr:last-child td {
  border-bottom: none;
}

table tbody tr:hover td {
  background: var(--color-card-hover);
}
</style>
