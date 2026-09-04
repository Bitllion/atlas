<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { IconLock, IconUser } from '@arco-design/web-vue/es/icon'
import { errorMessage } from '../api/client'
import { login } from '../stores/auth'
const router = useRouter(), form = reactive({ username: '', password: '' }), error = ref(''), submitting = ref(false)
async function submit() { if (!form.username.trim() || !form.password) return; error.value = ''; submitting.value = true; try { await login(form.username.trim(), form.password); await router.replace('/') } catch (requestError) { error.value = errorMessage(requestError) } finally { submitting.value = false } }
</script>
<template><main class="arco-login-page"><div class="login-brand"><span class="atlas-brand-mark">A</span><strong>Atlas</strong></div><a-card class="arco-login-card" :bordered="false"><div class="arco-login-header"><h1>登录 Atlas</h1><p>AI 基础设施智能运营管理平台</p></div><a-form :model="form" layout="vertical" @submit.prevent="submit"><a-form-item field="username" label="用户名" required><a-input v-model="form.username" name="username" autocomplete="username" autofocus placeholder="请输入用户名" size="large"><template #prefix><IconUser /></template></a-input></a-form-item><a-form-item field="password" label="密码" required><a-input-password v-model="form.password" name="password" autocomplete="current-password" placeholder="请输入密码" size="large"><template #prefix><IconLock /></template></a-input-password></a-form-item><a-alert v-if="error" type="error" class="arco-login-error">{{ error }}</a-alert><a-button type="primary" html-type="submit" long size="large" :loading="submitting" :disabled="!form.username.trim() || !form.password">登录</a-button></a-form><p class="demo-account">演示账号：admin / atlas123456</p></a-card><p class="login-copyright">Atlas · AI 基础设施智能运营管理平台</p></main></template>
