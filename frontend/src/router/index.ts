import { createRouter, createWebHistory } from 'vue-router'

import WelcomeView from '../views/WelcomeView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', name: 'welcome', component: WelcomeView }],
})
