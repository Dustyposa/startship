import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/init',
    name: 'init',
    component: () => import('../views/InitView.vue')
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('../views/SearchView.vue')
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/ChatView.vue')
  },
  {
    path: '/repo/:owner/:name',
    name: 'repo-detail',
    component: () => import('../views/RepoDetailView.vue')
  },
  {
    path: '/trends',
    name: 'trends',
    component: () => import('../views/TrendView.vue')
  },
  {
    path: '/network',
    name: 'network',
    component: () => import('../views/NetworkView.vue')
  },
  {
    path: '/collections',
    name: 'collections',
    component: () => import('../views/CollectionsView.vue')
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/TechProfileView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
