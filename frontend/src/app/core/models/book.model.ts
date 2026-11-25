/** Book as serialized by the Django REST API. */
export interface Book {
  readonly id: number;
  readonly title: string;
  readonly author: string;
  readonly isbn: string;
  readonly cost_usd: number;
  readonly selling_price_local: number | null;
  readonly stock_quantity: number;
  readonly category: string;
  readonly supplier_country: string;
  readonly created_at: string;
  readonly updated_at: string;
}

/** Writable fields accepted by POST /books and PUT /books/{id}. */
export interface BookPayload {
  title: string;
  author: string;
  isbn: string;
  cost_usd: number;
  stock_quantity: number;
  category: string;
  supplier_country: string;
  selling_price_local?: number | null;
}

/** Envelope shared by the list, search and low-stock endpoints. */
export interface PaginatedResponse<T> {
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: readonly T[];
}

export type ExchangeRateSource = 'live' | 'fallback';

/** Response of POST /books/{id}/calculate-price. */
export interface PriceCalculation {
  readonly book_id: number;
  readonly cost_usd: number;
  readonly exchange_rate: number;
  readonly cost_local: number;
  readonly margin_percentage: number;
  readonly selling_price_local: number;
  readonly currency: string;
  readonly calculation_timestamp: string;
  readonly exchange_rate_source: ExchangeRateSource;
}

/** Django REST Framework 400 body: field name -> list of messages. */
export type ApiFieldErrors = Record<string, string[]>;
