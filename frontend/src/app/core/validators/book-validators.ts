import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

const ISBN_DIGITS = /^\d{10}$|^\d{13}$/;
const TWO_LETTERS = /^[A-Za-z]{2}$/;

/** ISBN must keep 10 or 13 digits once hyphens and spaces are stripped. */
export const isbnValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value: unknown = control.value;
  if (typeof value !== 'string' || value.trim() === '') {
    return null;
  }
  const digits = value.replace(/[\s-]/g, '');
  return ISBN_DIGITS.test(digits) ? null : { isbn: true };
};

/** Supplier country is an ISO 3166-1 alpha-2 code: exactly two letters. */
export const supplierCountryValidator: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const value: unknown = control.value;
  if (typeof value !== 'string' || value.trim() === '') {
    return null;
  }
  return TWO_LETTERS.test(value.trim()) ? null : { supplierCountry: true };
};

/** Stock quantity must be a whole number. */
export const integerValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value: unknown = control.value;
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return { integer: true };
  }
  return Number.isInteger(value) ? null : { integer: true };
};
