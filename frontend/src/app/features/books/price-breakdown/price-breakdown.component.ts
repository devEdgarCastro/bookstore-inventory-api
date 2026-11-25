import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { PriceCalculation } from '../../../core/models/book.model';

/** Read-only presentation of the server side price calculation. */
@Component({
  selector: 'app-price-breakdown',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './price-breakdown.component.html',
  styleUrl: './price-breakdown.component.css',
})
export class PriceBreakdownComponent {
  readonly calculation = input.required<PriceCalculation>();
  readonly bookTitle = input('');

  protected readonly isFallback = computed(
    () => this.calculation().exchange_rate_source === 'fallback',
  );

  protected readonly sourceLabel = computed(() =>
    this.isFallback() ? 'Tasa de respaldo (fallback)' : 'Tasa de cambio en vivo',
  );
}
