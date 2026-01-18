import { ref, reactive } from 'vue'

export interface Toast {
  id: string
  type: 'success' | 'info' | 'warning' | 'error'
  title: string
  message?: string
  duration?: number
  autoClose?: boolean
}

class ToastService {
  private toasts = reactive<Toast[]>([])
  private nextId = 1

  show(toast: Omit<Toast, 'id'>): string {
    const id = `toast-${this.nextId++}`
    const newToast: Toast = {
      id,
      duration: 5000,
      autoClose: true,
      ...toast
    }

    this.toasts.push(newToast)

    if (newToast.autoClose) {
      setTimeout(() => {
        this.remove(id)
      }, newToast.duration)
    }

    return id
  }

  success(title: string, message?: string, options?: Partial<Toast>): string {
    return this.show({
      type: 'success',
      title,
      message,
      ...options
    })
  }

  info(title: string, message?: string, options?: Partial<Toast>): string {
    return this.show({
      type: 'info',
      title,
      message,
      ...options
    })
  }

  warning(title: string, message?: string, options?: Partial<Toast>): string {
    return this.show({
      type: 'warning',
      title,
      message,
      ...options
    })
  }

  error(title: string, message?: string, options?: Partial<Toast>): string {
    return this.show({
      type: 'error',
      title,
      message,
      autoClose: false, // Errors should be manually dismissed
      ...options
    })
  }

  remove(id: string): void {
    const index = this.toasts.findIndex(toast => toast.id === id)
    if (index > -1) {
      this.toasts.splice(index, 1)
    }
  }

  clear(): void {
    this.toasts.splice(0)
  }

  getToasts(): Toast[] {
    return this.toasts
  }
}

export const toastService = new ToastService()

// Composable for using toast service in components
export function useToast() {
  return {
    toasts: toastService.getToasts(),
    show: toastService.show.bind(toastService),
    success: toastService.success.bind(toastService),
    info: toastService.info.bind(toastService),
    warning: toastService.warning.bind(toastService),
    error: toastService.error.bind(toastService),
    remove: toastService.remove.bind(toastService),
    clear: toastService.clear.bind(toastService)
  }
}