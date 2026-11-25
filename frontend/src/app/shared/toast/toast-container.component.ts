import { Component, inject } from '@angular/core';
import { ToastService, ToastVariant } from './toast.service';

@Component({
  selector: 'app-toast-container',
  templateUrl: './toast-container.component.html',
  styleUrl: './toast-container.component.css',
})
export class ToastContainerComponent {
  private readonly toastService = inject(ToastService);

  protected readonly toasts = this.toastService.toasts;

  protected icon(variant: ToastVariant): string {
    switch (variant) {
      case 'success':
        return '✓';
      case 'error':
        return '!';
      default:
        return 'i';
    }
  }

  protected dismiss(id: number): void {
    this.toastService.dismiss(id);
  }
}
