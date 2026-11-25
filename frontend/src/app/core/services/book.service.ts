import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Book, BookPayload, PaginatedResponse, PriceCalculation } from '../models/book.model';

/**
 * Typed access to every endpoint exposed by the bookstore API.
 * The backend is served without a path prefix: http://localhost:8000/books
 */
@Injectable({ providedIn: 'root' })
export class BookService {
  private readonly http = inject(HttpClient);
  private readonly booksUrl = `${environment.apiBaseUrl}/books`;

  /** GET /books?page=&page_size= */
  list(page = 1, pageSize = 10): Observable<PaginatedResponse<Book>> {
    return this.http.get<PaginatedResponse<Book>>(this.booksUrl, {
      params: paginationParams(page, pageSize),
    });
  }

  /** GET /books/{id} */
  get(id: number): Observable<Book> {
    return this.http.get<Book>(`${this.booksUrl}/${id}`);
  }

  /** POST /books */
  create(payload: BookPayload): Observable<Book> {
    return this.http.post<Book>(this.booksUrl, payload);
  }

  /** PUT /books/{id} */
  update(id: number, payload: BookPayload): Observable<Book> {
    return this.http.put<Book>(`${this.booksUrl}/${id}`, payload);
  }

  /** DELETE /books/{id} */
  remove(id: number): Observable<void> {
    return this.http.delete<void>(`${this.booksUrl}/${id}`);
  }

  /** GET /books/search?category=&page=&page_size= */
  searchByCategory(category: string, page = 1, pageSize = 10): Observable<PaginatedResponse<Book>> {
    let params = paginationParams(page, pageSize);
    const trimmed = category.trim();
    if (trimmed !== '') {
      params = params.set('category', trimmed);
    }
    return this.http.get<PaginatedResponse<Book>>(`${this.booksUrl}/search`, { params });
  }

  /** GET /books/low-stock?threshold=&page=&page_size= */
  lowStock(threshold: number, page = 1, pageSize = 10): Observable<PaginatedResponse<Book>> {
    const params = paginationParams(page, pageSize).set('threshold', threshold);
    return this.http.get<PaginatedResponse<Book>>(`${this.booksUrl}/low-stock`, { params });
  }

  /** POST /books/{id}/calculate-price */
  calculatePrice(id: number): Observable<PriceCalculation> {
    return this.http.post<PriceCalculation>(`${this.booksUrl}/${id}/calculate-price`, null);
  }
}

function paginationParams(page: number, pageSize: number): HttpParams {
  return new HttpParams().set('page', Math.max(1, Math.trunc(page))).set('page_size', pageSize);
}
