import { Injectable, signal } from '@angular/core';

export type ToastVariant = 'success' | 'error' | 'info';

export interface Toast {
  readonly id: number;
  readonly message: string;
  readonly variant: ToastVariant;
}

const DEFAULT_DURATIONS: Record<ToastVariant, number> = {
  success: 4000,
  error: 7000,
  info: 5000,
};

/** Signal-based toast queue with per-toast auto dismissal. */
@Injectable({ providedIn: 'root' })
export class ToastService {
  private nextId = 1;
  private readonly timers = new Map<number, ReturnType<typeof setTimeout>>();
  private readonly state = signal<readonly Toast[]>([]);

  readonly toasts = this.state.asReadonly();

  show(message: string, variant: ToastVariant = 'info', durationMs?: number): number {
    const id = this.nextId++;
    this.state.update((toasts) => [...toasts, { id, message, variant }]);

    const duration = durationMs ?? DEFAULT_DURATIONS[variant];
    if (duration > 0) {
      this.timers.set(
        id,
        setTimeout(() => this.dismiss(id), duration),
      );
    }
    return id;
  }

  success(message: string, durationMs?: number): number {
    return this.show(message, 'success', durationMs);
  }

  error(message: string, durationMs?: number): number {
    return this.show(message, 'error', durationMs);
  }

  info(message: string, durationMs?: number): number {
    return this.show(message, 'info', durationMs);
  }

  dismiss(id: number): void {
    const timer = this.timers.get(id);
    if (timer !== undefined) {
      clearTimeout(timer);
      this.timers.delete(id);
    }
    this.state.update((toasts) => toasts.filter((toast) => toast.id !== id));
  }

  clear(): void {
    this.timers.forEach((timer) => clearTimeout(timer));
    this.timers.clear();
    this.state.set([]);
  }
}
