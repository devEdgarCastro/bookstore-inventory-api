import { TestBed } from '@angular/core/testing';
import { ToastService } from './toast.service';

describe('ToastService', () => {
  let service: ToastService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ToastService);
  });

  afterEach(() => {
    vi.useRealTimers();
    service.clear();
  });

  it('starts with no toasts', () => {
    expect(service.toasts()).toEqual([]);
  });

  it('adds a success toast with the given message', () => {
    service.success('Libro creado');
    expect(service.toasts().length).toBe(1);
    expect(service.toasts()[0].variant).toBe('success');
    expect(service.toasts()[0].message).toBe('Libro creado');
  });

  it('keeps every toast in insertion order', () => {
    service.success('primero');
    service.error('segundo');
    service.info('tercero');
    expect(service.toasts().map((toast) => toast.message)).toEqual([
      'primero',
      'segundo',
      'tercero',
    ]);
  });

  it('dismisses a single toast by id', () => {
    const id = service.success('uno');
    service.info('dos');
    service.dismiss(id);
    expect(service.toasts().map((toast) => toast.message)).toEqual(['dos']);
  });

  it('auto dismisses a toast once its duration elapses', () => {
    vi.useFakeTimers();
    service.info('temporal', 3000);
    expect(service.toasts().length).toBe(1);
    vi.advanceTimersByTime(2999);
    expect(service.toasts().length).toBe(1);
    vi.advanceTimersByTime(1);
    expect(service.toasts()).toEqual([]);
  });

  it('does not auto dismiss when the duration is not positive', () => {
    vi.useFakeTimers();
    service.error('permanente', 0);
    vi.advanceTimersByTime(60000);
    expect(service.toasts().length).toBe(1);
  });
});
