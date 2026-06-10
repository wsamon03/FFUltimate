<template>
  <div class="min-h-screen flex" style="background:var(--color-bg); color:var(--color-text-primary)">
    <!-- Desktop sidebar -->
    <TheSidebar class="hidden lg:flex" />

    <!-- Mobile sidebar overlay -->
    <Transition name="fade">
      <div
        v-if="ui.sidebarOpen"
        class="fixed inset-0 z-40 bg-black/60 lg:hidden"
        @click="ui.closeSidebar()"
      />
    </Transition>
    <Transition name="slide">
      <TheSidebar
        v-if="ui.sidebarOpen"
        class="fixed inset-y-0 left-0 z-50 lg:hidden"
        @close="ui.closeSidebar()"
      />
    </Transition>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 lg:pl-0">
      <TheHeader />
      <main class="flex-1 overflow-y-auto p-4 md:p-6 pb-20 lg:pb-6">
        <RouterView />
      </main>
    </div>

    <!-- Mobile bottom tab bar -->
    <TheMobileTabBar class="lg:hidden" />
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import TheSidebar from '@/components/layout/TheSidebar.vue'
import TheHeader from '@/components/layout/TheHeader.vue'
import TheMobileTabBar from '@/components/layout/TheMobileTabBar.vue'

const ui = useUiStore()
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
