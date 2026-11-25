import { FormControl } from '@angular/forms';
import { integerValidator, isbnValidator, supplierCountryValidator } from './book-validators';

describe('isbnValidator', () => {
  const errors = (value: string) => isbnValidator(new FormControl<string>(value));

  it('accepts a 13 digit ISBN', () => {
    expect(errors('9788437604947')).toBeNull();
  });

  it('accepts a 10 digit ISBN', () => {
    expect(errors('0306406152')).toBeNull();
  });

  it('accepts an ISBN with hyphens', () => {
    expect(errors('978-84-376-0494-7')).toBeNull();
  });

  it('accepts an ISBN with spaces', () => {
    expect(errors('978 84 376 0494 7')).toBeNull();
  });

  it('rejects an ISBN with 9 digits', () => {
    expect(errors('123456789')).toEqual({ isbn: true });
  });

  it('rejects an ISBN with 12 digits', () => {
    expect(errors('978843760494')).toEqual({ isbn: true });
  });

  it('rejects an ISBN with letters', () => {
    expect(errors('978-84-376-0494-X')).toEqual({ isbn: true });
  });

  it('ignores an empty value so that "required" can report it', () => {
    expect(errors('')).toBeNull();
  });
});

describe('supplierCountryValidator', () => {
  const errors = (value: string) => supplierCountryValidator(new FormControl<string>(value));

  it('accepts exactly two letters', () => {
    expect(errors('ES')).toBeNull();
  });

  it('rejects three letters', () => {
    expect(errors('ESP')).toEqual({ supplierCountry: true });
  });

  it('rejects digits', () => {
    expect(errors('E1')).toEqual({ supplierCountry: true });
  });

  it('ignores an empty value so that "required" can report it', () => {
    expect(errors('')).toBeNull();
  });
});

describe('integerValidator', () => {
  const errors = (value: number) => integerValidator(new FormControl<number>(value));

  it('accepts a whole number', () => {
    expect(errors(12)).toBeNull();
  });

  it('rejects a decimal number', () => {
    expect(errors(1.5)).toEqual({ integer: true });
  });
});
