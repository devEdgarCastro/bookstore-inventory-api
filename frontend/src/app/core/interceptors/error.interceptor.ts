import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { ToastService } from '../../shared/toast/toast.service';
import { ApiFieldErrors } from '../models/book.model';

const FIELD_LABELS: Record<string, string> = {
  title: 'Título',
  author: 'Autor',
  isbn: 'ISBN',
  cost_usd: 'Costo en USD',
  selling_price_local: 'Precio local',
  stock_quantity: 'Stock',
  category: 'Categoría',
  supplier_country: 'País del proveedor',
  non_field_errors: 'Datos',
  detail: 'Detalle',
};

/** Human readable label for a DRF field key. */
export function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

/** Type guard for the DRF field-error map returned with HTTP 400. */
export function isFieldErrorMap(body: unknown): body is ApiFieldErrors {
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    return false;
  }
  return Object.values(body).every(
    (value) => Array.isArray(value) && value.every((item) => typeof item === 'string'),
  );
}

/** Extract the field errors of a failed request; empty when there are none. */
export function extractFieldErrors(error: unknown): ApiFieldErrors {
  if (error instanceof HttpErrorResponse && isFieldErrorMap(error.error)) {
    return error.error;
  }
  return {};
}

/** Map an HTTP failure to a message shown to the user. */
export function describeHttpError(error: HttpErrorResponse): string {
  switch (error.status) {
    case 0:
      return 'No se pudo conectar con el servidor. Verifica que la API esté en ejecución.';
    case 400: {
      const fieldErrors = extractFieldErrors(error);
      const details = Object.entries(fieldErrors)
        .map(([field, messages]) => `${fieldLabel(field)}: ${messages.join(' ')}`)
        .join(' · ');
      return details === ''
        ? 'La solicitud contiene datos inválidos (400). Revisa el formulario.'
        : `Datos inválidos (400) — ${details}`;
    }
    case 404:
      return 'No se encontró el recurso solicitado (404). Puede que el libro ya no exista.';
    case 500:
      return 'Error interno del servidor (500). Inténtalo de nuevo en unos segundos.';
    case 503:
      return 'El servicio de tasas de cambio no está disponible (503). Inténtalo más tarde.';
    default:
      return `La operación falló (HTTP ${error.status}).`;
  }
}

/**
 * Reports every failed HTTP call as a toast and keeps the error flowing, so
 * components can still react (inline field errors, navigation, retries).
 */
export const errorInterceptor: HttpInterceptorFn = (request, next) => {
  const toast = inject(ToastService);

  return next(request).pipe(
    catchError((error: unknown) => {
      const message =
        error instanceof HttpErrorResponse
          ? describeHttpError(error)
          : 'Ha ocurrido un error inesperado.';
      toast.error(message);
      return throwError(() => error);
    }),
  );
};
