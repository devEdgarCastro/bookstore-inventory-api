import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'books' },
  {
    path: 'books',
    title: 'Inventario · Bookstore',
    loadComponent: () =>
      import('./features/books/book-list/book-list.component').then(
        (module) => module.BookListComponent,
      ),
  },
  {
    path: 'books/new',
    title: 'Nuevo libro · Bookstore',
    loadComponent: () =>
      import('./features/books/book-form/book-form.component').then(
        (module) => module.BookFormComponent,
      ),
  },
  {
    path: 'books/:id/edit',
    title: 'Editar libro · Bookstore',
    loadComponent: () =>
      import('./features/books/book-form/book-form.component').then(
        (module) => module.BookFormComponent,
      ),
  },
  { path: '**', redirectTo: 'books' },
];
