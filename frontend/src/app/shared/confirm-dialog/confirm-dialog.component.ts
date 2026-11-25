import { Component, ElementRef, HostListener, effect, input, output, viewChild } from '@angular/core';

/**
 * Reusable confirmation modal. The parent controls visibility through the
 * open input and reacts to the confirmed / cancelled outputs.
 */
@Component({
  selector: 'app-confirm-dialog',
  templateUrl: './confirm-dialog.component.html',
  styleUrl: './confirm-dialog.component.css',
})
export class ConfirmDialogComponent {
  readonly open = input(false);
  readonly title = input('¿Confirmar acción?');
  readonly message = input('');
  readonly confirmLabel = input('Confirmar');
  readonly cancelLabel = input('Cancelar');
  readonly busy = input(false);
  readonly tone = input<'danger' | 'default'>('danger');

  readonly confirmed = output<void>();
  readonly cancelled = output<void>();

  private readonly confirmButton = viewChild<ElementRef<HTMLButtonElement>>('confirmButton');

  constructor() {
    effect(() => {
      if (this.open()) {
        this.confirmButton()?.nativeElement.focus();
      }
    });
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    if (this.open() && !this.busy()) {
      this.cancelled.emit();
    }
  }

  protected onBackdropClick(): void {
    if (!this.busy()) {
      this.cancelled.emit();
    }
  }
}
