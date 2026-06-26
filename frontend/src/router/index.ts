import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Auth
    { path: '/login', component: () => import('@/pages/LoginPage.vue') },
    { path: '/register', component: () => import('@/pages/RegisterPage.vue') },
    { path: '/auth/callback', component: () => import('@/pages/AuthCallbackPage.vue') },

    // Public league join (no auth required)
    { path: '/leagues/join/:code', component: () => import('@/pages/leagues/LeagueJoinPage.vue') },

    // Authenticated shell
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('@/pages/DashboardPage.vue') },

        // Leagues
        { path: 'leagues', component: () => import('@/pages/leagues/LeaguesPage.vue') },
        { path: 'leagues/:id', component: () => import('@/pages/leagues/LeagueDetailPage.vue') },
        { path: 'leagues/:id/teams/:teamId', component: () => import('@/pages/leagues/TeamDetailPage.vue') },
        { path: 'leagues/:id/draft', component: () => import('@/pages/leagues/DraftPage.vue') },

        // NFL
        { path: 'nfl', component: () => import('@/pages/nfl/NflPage.vue') },
        { path: 'nfl/games', component: () => import('@/pages/nfl/NflGamesPage.vue') },
        { path: 'nfl/games/:id', component: () => import('@/pages/nfl/NflGameDetailPage.vue') },

        // Players
        { path: 'players', component: () => import('@/pages/players/PlayersPage.vue') },
        { path: 'players/:id', component: () => import('@/pages/players/PlayerDetailPage.vue') },

        // Other
        { path: 'favorites', component: () => import('@/pages/FavoritesPage.vue') },
        { path: 'profile', component: () => import('@/pages/ProfilePage.vue') },
      ],
    },

    // Fallback
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.bootPromise
  if (to.meta.requiresAuth && !auth.token) {
    return '/login'
  }
})

export default router
