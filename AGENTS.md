# LaLiga Value — zasady projektu

## Cel i bieżący zakres

LaLiga Value to aplikacja webowa do przyszłej analizy meczów hiszpańskiej
LaLigi i identyfikacji potencjalnie wartościowych kursów bukmacherskich.

Na obecnym etapie rozwijamy wyłącznie działający szkielet aplikacji. Nie
dodawaj bez wyraźnej prośby użytkownika:

- integracji z zewnętrznymi API sportowymi lub bukmacherskimi;
- pobierania wyników, statystyk albo kursów;
- modeli predykcyjnych, AI/ML, obliczeń prawdopodobieństwa lub EV;
- niepotrzebnych modułów i zależności.

## Stos technologiczny

- Frontend: React + Vite.
- Backend: Python + Django REST Framework.
- Baza danych: PostgreSQL.
- Uruchamianie lokalne: Docker Desktop + Docker Compose na Windows 11.
- Powłoka i instrukcje dla użytkownika: PowerShell.

## Struktura i konfiguracja

- `compose.yaml` definiuje usługi `db`, `backend` i `frontend`.
- `backend/` zawiera projekt Django; endpoint zdrowia to `GET /api/health/`.
- `frontend/` zawiera aplikację Vite i używa proxy `/api` do `backend:8000`.
- Zmienne środowiskowe są w lokalnym `.env`; plik ten nie może trafiać do Git.
- `.env.example` zawiera wyłącznie nazwy zmiennych i bezpieczne wartości
  przykładowe, nigdy prawdziwe sekrety.
- Nie zapisuj sekretów, haseł ani kluczy w kodzie, konfiguracji wersjonowanej
  ani historii Git.

## Historia kursów

- Kurs bukmacherski jest niezmiennym snapshotem, a nie bieżącą wartością do
  aktualizacji.
- Każde pobranie kursu zapisuj jako nowy rekord `OddsSnapshot` z dokładnym
  `captured_at`, także gdy kurs ma tę samą wartość co poprzednio.
- Nie nadpisuj ani nie usuwaj historycznych snapshotów przy kolejnym pobraniu.
  Historia jest potrzebna do analizy ruchu kursów przed meczem i uczciwego
  backtestingu przyszłych strategii.

## Sposób pracy

1. Zawsze najpierw sprawdź stan plików i istniejącą konfigurację. Nie zakładaj,
   że pliki opisane w zadaniu już istnieją.
2. Przed modyfikacją podaj krótki plan; wykonuj małe, logiczne etapy.
3. Czytaj zawartość istniejącego pliku przed jego zmianą. Nie nadpisuj go w
   ciemno.
4. Po każdym etapie wykonaj proporcjonalną weryfikację: np. `docker compose
   config`, test endpointu, `python manage.py check` lub build Vite.
5. Nie przechodź do kolejnego etapu, dopóki bieżący nie jest zweryfikowany.
6. Podawaj użytkownikowi konkretne polecenia PowerShell oraz katalog, w którym
   ma je uruchomić.

## Bezpieczeństwo i dane lokalne

- Nie wykonuj poleceń destrukcyjnych bez jednoznacznej potrzeby i zgody.
- Nie używaj `docker compose down -v`, nie usuwaj wolumenów PostgreSQL ani nie
  resetuj Git bez wyraźnej prośby użytkownika.
- Zachowuj istniejące zmiany użytkownika i nie modyfikuj plików niezwiązanych z
  aktualnym etapem.
- Przy zmianach struktury bazy stosuj migracje Django; nie manipuluj danymi
  bezpośrednio, jeśli migracja rozwiązuje problem.

## Kontrola jakości

Po zmianach dotyczących szkieletu preferuj następujące kontrole, zależnie od
zakresu:

```powershell
# Uruchamiaj w katalogu głównym projektu.
docker compose config
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://localhost:8000/api/health/
Invoke-RestMethod http://localhost:5173/api/health/
docker compose exec -T backend python manage.py check
docker compose exec -T frontend npm run build
```

Nie zatrzymuj działających usług po testach, chyba że użytkownik o to poprosi.
