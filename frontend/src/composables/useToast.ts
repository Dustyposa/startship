import { useToast as useVueToastification } from 'vue-toastification'

/**
 * Toast 通知组合式函数
 * 提供统一的通知接口
 */
export function useToast() {
  const toast = useVueToastification()

  return {
    /**
     * 成功通知
     */
    success(message: string, options?: any) {
      toast.success(message, {
        ...options,
        timeout: options?.timeout || 3000
      })
    },

    /**
     * 错误通知
     */
    error(message: string, options?: any) {
      toast.error(message, {
        ...options,
        timeout: options?.timeout || 5000  // 错误消息显示更长时间
      })
    },

    /**
     * 信息通知
     */
    info(message: string, options?: any) {
      toast.info(message, options)
    },

    /**
     * 警告通知
     */
    warning(message: string, options?: any) {
      toast.warning(message, options)
    },

    /**
     * 默认通知
     */
    show(message: string, options?: any) {
      toast(message, options)
    }
  }
}
