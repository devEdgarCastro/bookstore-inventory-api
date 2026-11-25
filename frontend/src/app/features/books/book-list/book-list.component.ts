import { DecimalPipe } from '@angular/common';
import { Component, HostListener, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Book, PriceCalculation } from '../../../core/models/book.model';
import { BookService } from '../../../core/services/book.service';
import { ConfirmDialogComponent } from '../../../shared/confirm-dialog/confirm-dialog.component';
import { ToastService } from '../../../shared/toast/toast.service';
import { PriceBreakdownComponent } from '../price-breakdown/price-breakdown.component';

type ListMode = 'all' | 'category' | 'lowStock';

/**
 * Inventory dashboard: catalog table, backend pagination, category and
 * low-stock filters and the price calculation action (S9, S11).
 */
@Component({
  selector: 'app-book-list',
  imports: [DecimalPipe, RouterLink, ConfirmDialogComponent, PriceBreakdownComponent],
  templateUrl: './book-list.component.html',
  styleUrl: './book-list.component.css',
})
export class BookListComponent implements OnInit {
  private readonly bookService = inject(BookService);
  private readonly toast = inject(ToastService);

  protected readonly pageSizeOptions: readonly number[] = [5, 10, 20, 50];

  protected readonly books = signal<readonly Book[]>([]);
  protected readonly count = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = signal(10);
  protected readonly loading = signal(false);
  protected readonly hasNext = signal(false);
  protected readonly hasPrevious = signal(false);

  protected readonly mode = signal<ListMode>('all');
  protected readonly appliedCategory = signal('');
  protected readonly appliedThreshold = signal(5);

  protected readonly categoryDraft = signal('');
  protected readonly thresholdDraft = signal(5);
  protected readonly lowStockOnly = signal(false);

  protected readonly calculatingId = signal<number | null>(null);
  protected readonly calculation = signal<PriceCalculation | null>(null);
  protected readonly calculationBook = signal<Book | null>(null);

  protected readonly deleting = signal<Book | null>(null);
  protected readonly deleteBusy = signal(false);

  protected readonly totalPages = computed(() =>
    Math.max(1, Math.ceil(this.count() / this.pageSize())),
  );

  protected readonly rangeStart = computed(() =>
    this.count() === 0 ? 0 : (this.page() - 1) * this.pageSize() + 1,
  );

  protected readonly rangeEnd = computed(() =>
    Math.min(this.page() * this.pageSize(), this.count()),
  );

  protected readonly activeFilterLabel = computed(() => {
    switch (this.mode()) {
      case 'category':
        return `Filtro por categoría: "${this.appliedCategory()}"`;
      case 'lowStock':
        return `Solo stock bajo (≤ ${this.appliedThreshold()} unidades)`;
      default:
        return 'Mostrando el catálogo completo';
    }
  });

  protected readonly deleteMessage = computed(() => {
    const book = this.deleting();
    return book === null
      ? ''
      : `El libro "${book.title}" (${book.isbn}) se eliminará del inventario. Esta acción no se puede deshacer.`;
  });

  protected readonly calculationTitle = computed(() => this.calculationBook()?.title ?? '');

  ngOnInit(): void {
    this.load();
  }

  protected onCategoryInput(event: Event): void {
    this.categoryDraft.set((event.target as HTMLInputElement).value);
  }

  protected onThresholdInput(event: Event): void {
    const value = (event.target as HTMLInputElement).valueAsNumber;
    this.thresholdDraft.set(Number.isFinite(value) ? Math.max(0, Math.trunc(value)) : 0);
  }

  protected onLowStockToggle(event: Event): void {
    this.lowStockOnly.set((event.target as HTMLInputElement).checked);
  }

  protected onPageSizeChange(event: Event): void {
    const value = Number((event.target as HTMLSelectElement).value);
    if (!Number.isFinite(value) || value <= 0) {
      return;
    }
    this.pageSize.set(value);
    this.page.set(1);
    this.load();
  }

  protected applyFilters(event: Event): void {
    event.preventDefault();
    const category = this.categoryDraft().trim();
    const useLowStock = this.lowStockOnly();

    this.appliedCategory.set(category);
    this.appliedThreshold.set(this.thresholdDraft());
    this.mode.set(useLowStock ? 'lowStock' : category === '' ? 'all' : 'category');
    this.page.set(1);
    this.load();
  }

  protected clearFilters(): void {
    this.categoryDraft.set('');
    this.thresholdDraft.set(5);
    this.lowStockOnly.set(false);
    this.appliedCategory.set('');
    this.appliedThreshold.set(5);
    this.mode.set('all');
    this.page.set(1);
    this.load();
  }

  protected goToPage(target: number): void {
    const bounded = Math.min(Math.max(1, target), this.totalPages());
    if (bounded === this.page() || this.loading()) {
      return;
    }
    this.page.set(bounded);
    this.load();
  }

  protected isLowStock(book: Book): boolean {
    return book.stock_quantity <= (this.mode() === 'lowStock' ? this.appliedThreshold() : 5);
  }

  protected askDelete(book: Book): void {
    this.deleting.set(book);
  }

  protected cancelDelete(): void {
    if (!this.deleteBusy()) {
      this.deleting.set(null);
    }
  }

  protected confirmDelete(): void {
    const book = this.deleting();
    if (book === null || this.deleteBusy()) {
      return;
    }
    this.deleteBusy.set(true);
    this.bookService.remove(book.id).subscribe({
      next: () => {
        this.deleteBusy.set(false);
        this.deleting.set(null);
        this.toast.success(`"${book.title}" se eliminó del inventario.`);
        if (this.books().length === 1 && this.page() > 1) {
          this.page.update((current) => current - 1);
        }
        this.load();
      },
      error: () => {
        this.deleteBusy.set(false);
        this.deleting.set(null);
      },
    });
  }

  protected calculate(book: Book): void {
    if (this.calculatingId() !== null) {
      return;
    }
    this.calculatingId.set(book.id);
    this.bookService.calculatePrice(book.id).subscribe({
      next: (calculation) => {
        this.calculatingId.set(null);
        this.calculation.set(calculation);
        this.calculationBook.set(book);
        this.books.update((books) =>
          books.map((item) =>
            item.id === calculation.book_id
              ? { ...item, selling_price_local: calculation.selling_price_local }
              : item,
          ),
        );
        this.toast.success(
          `Precio de venta de "${book.title}": ${calculation.selling_price_local.toFixed(2)} ${calculation.currency}.`,
        );
        if (calculation.exchange_rate_source === 'fallback') {
          this.toast.info(
            'La API de tasas no respondió: se aplicó la tasa de cambio de respaldo.',
          );
        }
      },
      error: () => {
        this.calculatingId.set(null);
      },
    });
  }

  protected closeCalculation(): void {
    this.calculation.set(null);
    this.calculationBook.set(null);
  }

  @HostListener('document:keydown.escape')
  protected onEscape(): void {
    if (this.calculation() !== null) {
      this.closeCalculation();
    }
  }

  private load(): void {
    this.loading.set(true);
    const page = this.page();
    const pageSize = this.pageSize();

    const request =
      this.mode() === 'category'
        ? this.bookService.searchByCategory(this.appliedCategory(), page, pageSize)
        : this.mode() === 'lowStock'
          ? this.bookService.lowStock(this.appliedThreshold(), page, pageSize)
          : this.bookService.list(page, pageSize);

    request.subscribe({
      next: (response) => {
        this.books.set(response.results);
        this.count.set(response.count);
        this.hasNext.set(response.next !== null);
        this.hasPrevious.set(response.previous !== null);
        this.loading.set(false);
      },
      error: () => {
        this.books.set([]);
        this.count.set(0);
        this.hasNext.set(false);
        this.hasPrevious.set(false);
        this.loading.set(false);
      },
    });
  }
}
