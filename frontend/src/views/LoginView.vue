<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { errorMessage } from '../api/client'
import { login } from '../stores/auth'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const error = ref('')
const submitting = ref(false)

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    await login(form.username.trim(), form.password)
    await router.replace('/')
  } catch (requestError) {
    error.value = errorMessage(requestError)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-card card">
      <header class="login-header">
        <span class="brand-mark">A</span>
        <div><h1>登录 Atlas</h1><p>AI 基础设施智能运营管理平台</p></div>
      </header>
      <form class="login-form" @submit.prevent="submit">
        <label>用户名<input v-model="form.username" name="username" autocomplete="username" required autofocus placeholder="请输入用户名" /></label>
        <label>密码<input v-model="form.password" name="password" type="password" autocomplete="current-password" required placeholder="请输入密码" /></label>
        <p v-if="error" class="login-error" role="alert">{{ error }}</p>
        <button class="button primary" type="submit" :disabled="submitting">{{ submitting ? '登录中…' : '登录' }}</button>
      </form>
      <p class="demo-account">演示账号：admin / atlas123456</p>
    </section>
  </main>
</template>
