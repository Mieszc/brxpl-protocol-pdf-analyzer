# Instrukcja obsługi: Delivery Protocol Analyzer

Niniejsza instrukcja opisuje, jak używać narzędzia **Delivery Protocol Analyzer** — programu pomocniczego, który automatycznie odczytuje pliki PDF z protokołami dostawców, wyciąga z nich wagi i procentowe zawartości metali szlachetnych, a następnie zapisuje je w jednym wspólnym arkuszu kalkulacyjnym gotowym do otwarcia w programie Excel.

---

## 1. Pierwsza konfiguracja (przygotowanie środowiska)

Aby odczytywać pliki PDF i wyświetlać kolorowe komunikaty, narzędzie korzysta z wbudowanego środowiska pomocniczego (`venv`) oraz drobnych bibliotek zewnętrznych.

Przed pierwszym uruchomieniem wykonaj poniższe kroki w celu przygotowania komputera:

### Krok 1: Otwórz terminal (wiersz poleceń)
Otwórz terminal w swoim systemie i przejdź do folderu z projektem:
* **macOS:** Otwórz program **Terminal**.
* **Windows (Standardowy wiersz poleceń):** Otwórz **Wiersz polecenia** (cmd).
* **Windows (PowerShell):** Otwórz **PowerShell**.

Użyj polecenia `cd`, aby wejść do katalogu z programem:
* **Wszystkie systemy operacyjne:**
  ```cmd
  cd sciezka/do/twojego/projektu/brxpl-protocol-pdf-analyzer
  ```

### Krok 2: Aktywuj środowisko pomocnicze
Uruchom odpowiednie polecenie dla swojego systemu i programu terminala, aby aktywować środowisko programu:

* **macOS (Terminal / Bash / Zsh):**
  ```bash
  source venv/bin/activate
  ```
* **Windows (Standardowy wiersz poleceń / cmd.exe):**
  ```cmd
  venv\Scripts\activate.bat
  ```
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
*(Po wpisaniu tego polecenia na początku linii w terminalu pojawi się znacznik `(venv)`, co oznacza, że środowisko pomocnicze jest aktywne i gotowe do pracy).*

### Krok 3: Instalacja lub aktualizacja bibliotek pomocniczych
Jeżeli autor programu wprowadzi nowe funkcje wymagające aktualizacji bibliotek, upewnij się, że środowisko pomocnicze jest aktywne `(venv)` i uruchom polecenie:
* **Wszystkie systemy operacyjne:**
  ```bash
  pip install -r requirements.txt
  ```

---

## 2. Bezpieczny zestaw folderów roboczych

Aby zagwarantować, że Twoje oryginalne pliki PDF nigdy nie zostaną uszkodzone, usunięte ani zagubione, program korzysta z bezpiecznego zestawu 3 folderów:

* **Folder Główny (Master Folder)**: Folder zawierający oryginalną, nienaruszoną bazę dokumentów. **Program tylko z niego odczytuje dane i nigdy nic w nim nie zmienia ani nie usuwa.**
* **Folder Archiwum (`archive/`)**: Po pomyślnym zakończeniu pracy programu, wszystkie poprawnie przetworzone oraz błędne pliki są automatycznie kopiowane tutaj do oddzielnych podfolderów, z zachowaniem oryginalnej struktury katalogów. Dzięki temu zawsze możesz podejrzeć kopie plików dla danego uruchomienia.
* **Folder Wyjściowy (Output Folder)**: Folder, w którym program zapisuje końcowe raporty w formacie CSV gotowe do otwarcia w programie Excel.

> [!NOTE]
> Z programu został usunięty koncept Dropzone. Od teraz uruchamiasz analizę bezpośrednio na bazie Master, a program wykonuje analizę tylko do odczytu, całkowicie chroniąc oryginalne pliki.

---

## 3. Uruchomienie programu

Gdy środowisko pomocnicze jest aktywne `(venv)`, uruchom program wpisując polecenie:

* **Wszystkie systemy operacyjne:**
  ```bash
  python analyze.py
  ```
  *(Na systemie Windows można również użyć: `py analyze.py`)*

---

## 4. Pytania konfiguracyjne i potwierdzenie startu

Po uruchomieniu program automatycznie sprawdza uprawnienia do folderów i zadaje kilka podstawowych pytań. Przy pytaniach zawierających domyślne ścieżki w nawiasach kwadratowych `[...]` możesz po prostu nacisnąć **Enter**, aby je zaakceptować, lub wpisać nową ścieżkę:

1. **`[1/3] Output folder [sciezka_domyslna]:`**
   * Wyświetla docelową lokalizację zapisu raportu. Naciśnij **Enter**, aby zatwierdzić, lub wpisz inną ścieżkę do folderu.
2. **`[2/3] Date from (DD.MM.YYYY):`**
   * Wpisz datę początkową okresu rozliczeniowego (np. `01.05.2026`).
3. **`[3/3] Date to (DD.MM.YYYY):`**
   * Wpisz datę końcową okresu (np. `07.06.2026`).

### Podsumowanie i start:
Po przejściu konfiguracji program wyświetli podsumowanie:
```text
─────────────────────────────────────────────
  Ready to run
  Window:    01.05.2026 → 07.06.2026
  Output:    /Users/MIESZKO/.../output-protocols-analyzed
─────────────────────────────────────────────
  Press Enter to start or Ctrl+C to abort: 
```
* Naciśnij **Enter**, aby rozpocząć przetwarzanie i analizę dokumentów.
* Naciśnij **Ctrl+C** na klawiaturze, aby anulować operację bez wprowadzania jakichkolwiek zmian.

---

## 5. Weryfikacja wyników i czyszczenie archiwum

Gdy program pomyślnie przetworzy pliki i zapisze arkusz CSV, wyświetli w terminalu komunikat dotyczący zarządzania miejscem na dysku:

1. **Zweryfikuj raport:** Otwórz nowo utworzony plik CSV w programie Excel i sprawdź, czy wagi i sumy są poprawne.
2. **Przejrzyj kopie plików:** Pomyślnie przetworzone pliki zostały skopiowane do folderu `archive/samples_run_X`, a pliki, z którymi wystąpił błąd, do `archive/failed_samples_run_X`. Możesz tam zajrzeć, jeśli potrzebujesz sprawdzić konkretne pliki PDF.
3. **Wybierz krok czyszczenia:**
   * **Jeśli wyniki są poprawne (Usuń kopie z archiwum):** Naciśnij **Enter**. Program automatycznie usunie tymczasowe katalogi z folderu `archive/`, aby nie zaśmiecać dysku.
   * **Jeśli chcesz zachować kopie plików (Zachowaj kopie):** Naciśnij **Ctrl+C**. Narzędzie zakończy działanie, pozostawiając skopiowane pliki w folderze `archive/` nienaruszone.

---

## 6. Wyłączenie narzędzia (dezaktywacja środowiska pomocniczego)

Po zakończeniu pracy w linii komend nadal będzie widoczny znacznik `(venv)`. Aby bezpiecznie zamknąć środowisko pomocnicze, wykonaj następujące kroki:

### Krok 1: Wyłącz środowisko pomocnicze
Wpisz poniższe polecenie i naciśnij **Enter**:
* **Wszystkie systemy operacyjne:**
  ```bash
  deactivate
  ```
*(Znacznik `(venv)` zniknie z początku linii, co oznacza powrót do normalnego stanu systemu).*

### Krok 2: Zamknij okno
Teraz możesz bezpiecznie zamknąć okno programu Terminal, Wiersza poleceń lub PowerShell.

---

## 7. Co zobaczysz w terminalu (wyniki i komunikaty)

W trakcie działania program wypisuje w terminalu status każdego sprawdzanego pliku PDF:

* **`[OK]`**: Plik PDF został poprawnie odczytany, dane zostały dodane do raportu, a jego kopia zostanie zarchiwizowana do folderu pomyślnego uruchomienia.
  ```text
  [OK]  Cronimet Nordic / 2026 / 26002238  →  finalized 24.03.2026
  ```
* **`[--]`**: Plik PDF został odczytany poprawnie, lecz jego data dostawy/otrzymania wykracza poza wybrany zakres dat, dlatego został pominięty.
  ```text
  [--]  Cronimet Nordic / 2026 / 57100-1  →  finalized 12.04.2026  (outside window)
  ```
* **`[FAIL]`**: Napotkano problem z odczytem konkretnego pliku (np. uszkodzony plik PDF, obraz skanowany zamiast tekstu cyfrowego, brakujące wagi). **Program nie zatrzymuje całej analizy** — pomija ten plik, wypisuje błąd w kolorze czerwonym i przechodzi do kolejnych. Liczba takich błędów zostanie podsumowana na końcu jako `Nieudane protokoły (failed)`.
* **`[ERR]`**: Wystąpił błąd krytyczny i program natychmiast przerwał działanie. **W takim przypadku raport CSV nie zostanie zapisany**, aby zapobiec generowaniu niepełnych lub błędnych danych.

### Błędy krytyczne powodujące natychmiastowe zatrzymanie:
* **Wykrycie duplikatu pozycji**: Dwa lub więcej plików PDF w tym samym folderze dostawy zgłaszają ten sam numer pozycji (`Pos.`).
* **Weryfikacja bazy Master**: Jeśli w folderze głównym (Master) nie ma plików (folder jest pusty lub ścieżka jest nieprawidłowa).

---

## 8. Zrozumienie wygenerowanego arkusza (raportu)

Raporty zapisywane są w folderze wyjściowym (Output):

### Format nazwy pliku:
```text
DeliveryReport_{DDMMYYYY}_{DDMMYYYY}.csv
```
*Przykład:* `DeliveryReport_01012025_07062026.csv`

> [!NOTE]
> Jeżeli plik o takiej nazwie już istnieje w folderze wyjściowym, program automatycznie doda kolejny numer na końcu (np. `_2.csv`, `_3.csv`), aby uniknąć nadpisania wcześniejszych wyników.

### Struktura pliku CSV:
* **Zgodność z polską wersją programu Excel**: Raport używa średnika `;` jako separatora kolumn, co pozwala na automatyczne otwieranie pliku w programach Excel na europejskich systemach bez potrzeby ręcznego importu tekstu.
* **Formatowanie liczb (Przecinki)**: Wszystkie liczby zmiennoprzecinkowe używają przecinka `,` jako separatora dziesiętnego (np. `22140,000` lub `0,30`), co zapewnia bezpośrednią kompatybilność z polskimi ustawieniami regionalnymi.
* **Sortowanie wierszy**: Wyjściowe wiersze sortowane są według:
  1. **Smelter Code** (najpierw huty BRX, potem KK).
  2. **Numeru dostawy** (rosnąco).
  3. **Numeru pozycji** (rosnąco).
* **Wiersz Podsumowania (Total)**: Ostatni wiersz raportu zawiera podsumowanie wag (`Quantity kg`, `Dry quant. kg`) oraz całkowitych ilości metali szlachetnych w kilogramach.

---

## 9. Zmiana domyślnych ścieżek (konfiguracja)

Domyślne katalogi robocze są skonfigurowane w pliku `analyze.py` na samym początku w sekcji `# PATH CONFIGURATION`:
* `OUTPUT_FOLDER`: Domyślna ścieżka zapisu raportów CSV.
* `MASTER_FOLDER`: Ścieżka do oryginalnej bazy Master (zabezpieczenie).
* `ARCHIVE_FOLDER`: Ścieżka do tymczasowego folderu archiwum.

### Uwaga dotycząca ścieżek systemowych Windows
W systemie Windows ścieżki do folderów zawierają ukośniki wsteczne (`\`). Aby Python prawidłowo interpretował te ścieżki i nie traktował ukośników jako znaków specjalnych, poprzedź cały ciąg znaków literą `r` (tzw. raw string):

```python
OUTPUT_FOLDER = r"C:\Uzytkownicy\Jan\Dokumenty\RaportyDostaw"
MASTER_FOLDER = r"C:\Uzytkownicy\Jan\Pulpit\brxpl\Dostawcy"
ARCHIVE_FOLDER = r"C:\Uzytkownicy\Jan\Pulpit\brxpl-protocol-pdf-analyzer\archive"
```
