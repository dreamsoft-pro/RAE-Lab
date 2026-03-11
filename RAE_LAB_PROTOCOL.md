# 🔬 RAE-Lab: Laboratoryjny Protokół Analizy

Ten moduł jest sercem analitycznym RAE-Suite. Zbiera dane z mikro-evaluatorów i wylicza globalne wskaźniki jakości.

## Metryki Główne:
1. **Success Rate**: Procent zadań zakończonych bez poprawek.
2. **Token Efficiency (Lean)**: Ile merytorycznego kodu / wyniku generujemy na 1000 tokenów.
3. **Kaizen Velocity**: Szybkość poprawy systemu w czasie.

## Struktura:
- `/experiments`: Surowe dane JSON z każdego wykonania zadania.
- `/insights`: Zagregowane raporty dla użytkownika.

## Kontrakt:
Każdy moduł (Phoenix, Hive) musi po zakończeniu pracy zapisać plik JSON w `/experiments` o formacie:
```json
{
  "module": "string",
  "task_id": "uuid",
  "score": "float",
  "lean_metrics": {},
  "timestamp": "iso8601"
}
```
