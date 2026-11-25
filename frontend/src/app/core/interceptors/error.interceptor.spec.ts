import {
  HttpClient,
  HttpErrorResponse,
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ToastService } from '../../shared/toast/toast.service';
import { errorInterceptor } from './error.interceptor';

describe('errorInterceptor', () => {
  let httpMock: HttpTestingController;
  let toasts: ToastService;
  let failure: HttpErrorResponse | undefined;

  beforeEach(() => {
    failure = undefined;
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([errorInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    httpMock = TestBed.inject(HttpTestingController);
    toasts = TestBed.inject(ToastService);
  });

  afterEach(() => httpMock.verify());

  function send(url: string, status: number, body: object): void {
    TestBed.inject(HttpClient)
      .get(url)
      .subscribe({ error: (error: HttpErrorResponse) => (failure = error) });
    httpMock.expectOne(url).flush(body, { status, statusText: 'Error' });
  }

  it('rethrows the 400 error and surfaces the field messages', () => {
    send('/books', 400, { isbn: ['Ya existe un libro con este ISBN.'] });
    expect(failure?.status).toBe(400);
    expect(toasts.toasts().length).toBe(1);
    expect(toasts.toasts()[0].variant).toBe('error');
    expect(toasts.toasts()[0].message).toContain('Ya existe un libro con este ISBN.');
  });

  it('maps 404 to a not found message', () => {
    send('/books/99', 404, { detail: 'No encontrado.' });
    expect(failure?.status).toBe(404);
    expect(toasts.toasts()[0].message).toContain('404');
  });

  it('maps 500 to a server error message', () => {
    send('/books', 500, { detail: 'boom' });
    expect(failure?.status).toBe(500);
    expect(toasts.toasts()[0].message).toContain('500');
  });

  it('maps 503 to an exchange rate availability message', () => {
    send('/books/1/calculate-price', 503, { detail: 'unavailable' });
    expect(failure?.status).toBe(503);
    expect(toasts.toasts()[0].message).toContain('503');
  });
});
