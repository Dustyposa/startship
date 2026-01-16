import { ref } from 'vue'

interface ConfirmOptions {
  title: string
  message?: string
  subMessage?: string
  icon?: string
  warning?: string
  details?: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  type?: 'danger' | 'warning' | 'info' | 'success'
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

interface ConfirmState extends Required<Omit<ConfirmOptions, 'warning' | 'details' | 'subMessage'>> {
  show: boolean
  warning?: string
  details?: string
  subMessage?: string
  loading: boolean
  resolve: ((value: boolean) => void) | null
}

const state = ref<ConfirmState>({
  show: false,
  title: '',
  message: '',
  subMessage: '',
  icon: '',
  warning: '',
  details: '',
  confirmText: '确认',
  cancelText: '取消',
  showCancel: true,
  type: 'danger',
  size: 'md',
  loading: false,
  resolve: null
})

export function useConfirm() {
  const confirm = (options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      state.value = {
        show: true,
        title: options.title,
        message: options.message || '',
        subMessage: options.subMessage || '',
        icon: options.icon || '',
        warning: options.warning || '',
        details: options.details || '',
        confirmText: options.confirmText || '确认',
        cancelText: options.cancelText || '取消',
        showCancel: options.showCancel !== false,
        type: options.type || 'danger',
        size: options.size || 'md',
        loading: false,
        resolve
      }
    })
  }

  const confirmWithLoading = async (
    options: ConfirmOptions,
    action: () => Promise<void>
  ): Promise<boolean> => {
    const result = await confirm(options)
    if (!result) return false

    state.value.loading = true
    try {
      await action()
      return true
    } catch (error) {
      console.error('Action failed:', error)
      return false
    } finally {
      state.value.loading = false
      state.value.show = false
    }
  }

  const handleConfirm = () => {
    if (state.value.resolve) {
      state.value.resolve(true)
    }
  }

  const handleCancel = () => {
    if (state.value.resolve && !state.value.loading) {
      state.value.resolve(false)
      state.value.show = false
    }
  }

  // Helper methods for common confirmations
  const confirmDelete = (itemType: string, itemName?: string): Promise<boolean> => {
    return confirm({
      title: '确认删除',
      type: 'danger',
      icon: '🗑️',
      message: itemName ? `确定要删除 "${itemName}" 吗？` : `确定要删除此${itemType}吗？`,
      subMessage: '此操作无法撤销',
      confirmText: '删除',
      cancelText: '取消'
    })
  }

  const confirmRemove = (itemType: string, itemName?: string): Promise<boolean> => {
    return confirm({
      title: '确认移除',
      type: 'warning',
      icon: '📤',
      message: itemName ? `确定要将 "${itemName}" 从${itemType}中移除吗？` : `确定要移除此${itemType}吗？`,
      confirmText: '移除',
      cancelText: '取消'
    })
  }

  const confirmClear = (itemType: string): Promise<boolean> => {
    return confirm({
      title: '确认清空',
      type: 'warning',
      icon: '🧹',
      message: `确定要清空所有${itemType}吗？`,
      subMessage: '此操作无法撤销',
      confirmText: '清空',
      cancelText: '取消'
    })
  }

  const confirmAction = (action: string, description: string): Promise<boolean> => {
    return confirm({
      title: `确认${action}`,
      type: 'info',
      message: description,
      confirmText: action,
      cancelText: '取消'
    })
  }

  return {
    state,
    confirm,
    confirmWithLoading,
    handleConfirm,
    handleCancel,
    confirmDelete,
    confirmRemove,
    confirmClear,
    confirmAction
  }
}
