import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'

// Configure axios defaults
axios.defaults.timeout = 10000 // 10 second timeout

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Toast, {
  timeout: 3000,
  position: 'top-right',
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  icon: true,
  rtl: false
})
app.mount('#app')
