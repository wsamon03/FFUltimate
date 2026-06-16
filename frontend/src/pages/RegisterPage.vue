<template>
  <div class="w-full max-w-sm mx-auto">
    <!-- Branding -->
    <div class="text-center mb-8">
      <div class="w-14 h-14 rounded-2xl flex items-center justify-center text-white text-xl font-bold mx-auto mb-4"
        style="background: var(--color-primary)">
        FF
      </div>
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary)">
        {{ themeStore.appName }}
      </h1>
      <p class="mt-1 text-sm" style="color: var(--color-text-secondary)">
        Create your account
      </p>
    </div>

    <!-- Register card -->
    <div class="rounded-2xl border p-8" style="background: var(--color-card); border-color: var(--color-border)">
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--color-text-secondary)">Email</label>
          <input
            v-model="email"
            type="email"
            autocomplete="email"
            required
            class="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-primary"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
        </div>

        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--color-text-secondary)">
            Display Name <span style="color: var(--color-text-secondary)">(optional)</span>
          </label>
          <input
            v-model="displayName"
            type="text"
            autocomplete="name"
            maxlength="255"
            class="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-primary"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
        </div>

        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--color-text-secondary)">Password</label>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            required
            class="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-primary"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
          <p class="text-xs mt-1" style="color: var(--color-text-secondary)">Minimum 12 characters</p>
        </div>

        <div>
          <label class="block text-xs font-medium mb-1" style="color: var(--color-text-secondary)">Confirm Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
            class="w-full px-3 py-2 rounded-lg border text-sm outline-none focus:ring-2 focus:ring-primary"
            style="background: var(--color-bg); border-color: var(--color-border); color: var(--color-text-primary)"
          />
        </div>

        <p v-if="error" class="text-xs text-red-400">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full px-4 py-2.5 rounded-lg text-sm font-medium text-white transition-opacity disabled:opacity-60"
          style="background: var(--color-primary)"
        >
          {{ loading ? 'Creating account…' : 'Create Account' }}
        </button>
      </form>
    </div>

    <!-- Login link -->
    <p class="text-center text-sm mt-4" style="color: var(--color-text-secondary)">
      Already have an account?
      <RouterLink to="/login" class="font-medium hover:underline" style="color: var(--color-primary)">
        Sign in
      </RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { registerLocal, getMe } from '@/api/auth'

const themeStore = useThemeStore()
const authStore = useAuthStore()
const router = useRouter()

const email = ref('')
const displayName = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (password.value.length < 12) {
    error.value = 'Password must be at least 12 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }

  loading.value = true
  try {
    const { access_token } = await registerLocal(
      email.value,
      password.value,
      displayName.value || undefined,
    )
    authStore.setToken(access_token)
    authStore.user = await getMe()
    router.replace('/dashboard')
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (detail === 'EMAIL_EXISTS') {
      error.value = 'An account with this email already exists.'
    } else {
      error.value = detail ?? 'Registration failed. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>
