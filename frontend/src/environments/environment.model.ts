/** Shape shared by every environment file (kept apart so fileReplacements never breaks the import). */
export interface Environment {
  readonly production: boolean;
  readonly apiBaseUrl: string;
}
