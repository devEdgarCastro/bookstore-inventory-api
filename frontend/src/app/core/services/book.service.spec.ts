import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../environments/environment';
import { Book, BookPayload, PaginatedResponse } from '../models/book.model';
import { BookService } from './book.service';

const emptyPage: PaginatedResponse<Book> = { count: 0, next: null, previous: null, results: [] };

const payload: BookPayload = {
  title: 'El Quijote',
  author: 'Miguel de Cervantes',
  isbn: '978-84-376-0494-7',
  cost_usd: 15.99,
  stock_quantity: 25,
  category: 'Literatura Clasica',
  supplier_country: 'ES',
};

describe('BookService', () => {
  let service: BookService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BookService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('requests a page with page and page_size query params', () => {
    let received: PaginatedResponse<Book> | undefined;
    service.list(2, 5).subscribe((page) => (received = page));

    const request = httpMock.expectOne(
      (req) => req.url === `${environment.apiBaseUrl}/books` && req.method === 'GET',
    );
    expect(request.request.params.get('page')).toBe('2');
    expect(request.request.params.get('page_size')).toBe('5');
    request.flush(emptyPage);
    expect(received).toEqual(emptyPage);
  });

  it('requests a single book', () => {
    service.get(7).subscribe();
    const request = httpMock.expectOne(`${environment.apiBaseUrl}/books/7`);
    expect(request.request.method).toBe('GET');
    request.flush({ id: 7 });
  });

  it('creates a book with POST', () => {
    service.create(payload).subscribe();
    const request = httpMock.expectOne(`${environment.apiBaseUrl}/books`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(payload);
    request.flush({ id: 1, ...payload });
  });

  it('updates a book with PUT', () => {
    service.update(7, payload).subscribe();
    const request = httpMock.expectOne(`${environment.apiBaseUrl}/books/7`);
    expect(request.request.method).toBe('PUT');
    expect(request.request.body).toEqual(payload);
    request.flush({ id: 7, ...payload });
  });

  it('deletes a book with DELETE', () => {
    service.remove(7).subscribe();
    const request = httpMock.expectOne(`${environment.apiBaseUrl}/books/7`);
    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });
  });

  it('searches by category keeping pagination params', () => {
    service.searchByCategory('Novela', 3, 10).subscribe();
    const request = httpMock.expectOne(
      (req) => req.url === `${environment.apiBaseUrl}/books/search` && req.method === 'GET',
    );
    expect(request.request.params.get('category')).toBe('Novela');
    expect(request.request.params.get('page')).toBe('3');
    expect(request.request.params.get('page_size')).toBe('10');
    request.flush(emptyPage);
  });

  it('requests low stock books with a threshold', () => {
    service.lowStock(4, 1, 10).subscribe();
    const request = httpMock.expectOne(
      (req) => req.url === `${environment.apiBaseUrl}/books/low-stock` && req.method === 'GET',
    );
    expect(request.request.params.get('threshold')).toBe('4');
    expect(request.request.params.get('page')).toBe('1');
    expect(request.request.params.get('page_size')).toBe('10');
    request.flush(emptyPage);
  });

  it('posts to the calculate-price action', () => {
    service.calculatePrice(9).subscribe();
    const request = httpMock.expectOne(`${environment.apiBaseUrl}/books/9/calculate-price`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toBeNull();
    request.flush({ book_id: 9 });
  });
});
