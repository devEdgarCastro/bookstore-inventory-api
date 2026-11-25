import { Component, OnInit, computed, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { extractFieldErrors, fieldLabel } from '../../../core/interceptors/error.interceptor';
import { BookPayload } from '../../../core/models/book.model';
import { BookService } from '../../../core/services/book.service';
import {
  integerValidator,
  isbnValidator,
  supplierCountryValidator,
} from '../../../core/validators/book-validators';
import { ToastService } from '../../../shared/toast/toast.service';

interface BookFormControls {
  title: FormControl<string>;
  author: FormControl<string>;
  isbn: FormControl<string>;
  cost_usd: FormControl<number | null>;
  stock_quantity: FormControl<number | null>;
  category: FormControl<string>;
  supplier_country: FormControl<string>;
  /** Server owned; kept so an UPDATE never discards a calculated price. */
  selling_price_local: FormControl<number | null>;
}

const MESSAGES: Record<string, Record<string, string>> = {
  title: { required: 'El título es obligatorio.', maxlength: 'Máximo 255 caracteres.' },
  author: { required: 'El autor es obligatorio.', maxlength: 'Máximo 255 caracteres.' },
  isbn: {
    required: 'El ISBN es obligatorio.',
    isbn: 'El ISBN debe tener 10 o 13 dígitos (puedes usar guiones o espacios).',
  },
  cost_usd: {
    required: 'El costo en USD es obligatorio.',
    min: 'El costo debe ser mayor que 0.',
  },
  stock_quantity: {
    required: 'La cantidad en stock es obligatoria.',
    min: 'El stock no puede ser negativo.',
    integer: 'Usa un número entero de unidades.',
  },
  category: { required: 'La categoría es obligatoria.', maxlength: 'Máximo 120 caracteres.' },
  supplier_country: {
    required: 'El país del proveedor es obligatorio.',
    supplierCountry: 'Usa un código de 2 letras (por ejemplo ES).',
  },
};

/** Create and edit form for a book (S10). */
@Component({
  selector: 'app-book-form',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './book-form.component.html',
  styleUrl: './book-form.component.css',
})
export class BookFormComponent implements OnInit {
  private readonly bookService = inject(BookService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  protected readonly form = new FormGroup<BookFormControls>({
    title: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(255)],
    }),
    author: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(255)],
    }),
    isbn: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, isbnValidator],
    }),
    cost_usd: new FormControl<number | null>(null, {
      validators: [Validators.required, Validators.min(0.01)],
    }),
    stock_quantity: new FormControl<number | null>(null, {
      validators: [Validators.required, Validators.min(0), integerValidator],
    }),
    category: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.maxLength(120)],
    }),
    supplier_country: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, supplierCountryValidator],
    }),
    selling_price_local: new FormControl<number | null>(null),
  });

  protected readonly loading = signal(false);
  protected readonly saving = signal(false);
  protected readonly serverErrors = signal<Record<string, string[]>>({});

  protected readonly bookId = computed<number | null>(() => {
    const raw = this.route.snapshot.paramMap.get('id');
    if (raw === null) {
      return null;
    }
    const parsed = Number(raw);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  });

  protected readonly isEdit = computed(() => this.bookId() !== null);

  protected readonly formError = computed(() => {
    const messages = this.serverErrors()['non_field_errors'];
    return messages === undefined ? '' : messages.join(' ');
  });

  /** Server errors that have no inline field to render next to. */
  protected readonly otherServerErrors = computed(() =>
    Object.entries(this.serverErrors())
      .filter(([field]) => field !== 'non_field_errors' && !(field in this.form.controls))
      .map(([field, messages]) => ({ field, messages })),
  );

  ngOnInit(): void {
    this.clearServerErrorsOnEdit();

    const id = this.bookId();
    if (id === null) {
      return;
    }

    this.loading.set(true);
    this.bookService.get(id).subscribe({
      next: (book) => {
        this.form.patchValue({
          title: book.title,
          author: book.author,
          isbn: book.isbn,
          cost_usd: book.cost_usd,
          stock_quantity: book.stock_quantity,
          category: book.category,
          supplier_country: book.supplier_country,
          selling_price_local: book.selling_price_local,
        });
        this.form.markAsPristine();
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        void this.router.navigate(['/books']);
      },
    });
  }

  protected fieldError(name: keyof BookFormControls): string {
    const control = this.form.controls[name];
    if (!control.invalid || !(control.touched || control.dirty)) {
      return '';
    }
    const messages = MESSAGES[name] ?? {};
    for (const key of Object.keys(control.errors ?? {})) {
      const message = messages[key];
      if (message !== undefined) {
        return message;
      }
    }
    return 'Valor inválido.';
  }

  protected serverError(field: string): string {
    const messages = this.serverErrors()[field];
    return messages === undefined ? '' : messages.join(' ');
  }

  protected serverErrorLabel(field: string): string {
    return fieldLabel(field);
  }

  protected submit(event: Event): void {
    event.preventDefault();
    if (this.saving()) {
      return;
    }

    this.form.markAllAsTouched();
    if (this.form.invalid) {
      this.toast.info('Revisa los campos marcados antes de guardar.');
      return;
    }

    const raw = this.form.getRawValue();
    const payload: BookPayload = {
      title: raw.title.trim(),
      author: raw.author.trim(),
      isbn: raw.isbn.trim(),
      cost_usd: raw.cost_usd ?? 0,
      stock_quantity: raw.stock_quantity ?? 0,
      category: raw.category.trim(),
      supplier_country: raw.supplier_country.trim().toUpperCase(),
    };
    if (raw.selling_price_local !== null) {
      payload.selling_price_local = raw.selling_price_local;
    }

    const id = this.bookId();
    this.saving.set(true);
    this.serverErrors.set({});

    const request = id === null
      ? this.bookService.create(payload)
      : this.bookService.update(id, payload);

    request.subscribe({
      next: (book) => {
        this.saving.set(false);
        this.toast.success(
          id === null
            ? `"${book.title}" se registró en el inventario.`
            : `"${book.title}" se actualizó correctamente.`,
        );
        void this.router.navigate(['/books']);
      },
      error: (error: unknown) => {
        this.saving.set(false);
        const fieldErrors = extractFieldErrors(error);
        this.serverErrors.set(fieldErrors);
        if (Object.keys(fieldErrors).length > 0) {
          this.form.markAllAsTouched();
        }
      },
    });
  }

  private clearServerErrorsOnEdit(): void {
    for (const name of Object.keys(this.form.controls) as (keyof BookFormControls)[]) {
      const control: AbstractControl = this.form.controls[name];
      control.valueChanges.subscribe(() => {
        const current = this.serverErrors();
        if (current[name] === undefined) {
          return;
        }
        const next = { ...current };
        delete next[name];
        this.serverErrors.set(next);
      });
    }
  }
}
