# RAE-Lab: Intelligence Observatory & Research Environment 🔬

RAE-Lab to centrum analityczne i badawcze ekosystemu RAE-Suite. Jego zadaniem jest zbieranie metryk z pracy wszystkich agentów, analizowanie ich wydajności i generowanie wniosków optymalizacyjnych dla strategii **Kaizen** i **Lean**.

## 🧬 Główne Funkcje

1.  **Experiment Manager**: System zbierania raportów JSON z modułów Hive i Phoenix. Każda akcja inżynieryjna jest traktowana jako eksperyment o mierzalnym wyniku.
2.  **Metrics Aggregator**: Silnik wyliczający globalne wskaźniki systemu:
    *   **Success Rate**: Procent zadań wykonanych poprawnie w pierwszej iteracji.
    *   **Token Econometrics (Lean)**: Analiza kosztów i wydajności modeli (Gemini vs DeepSeek vs Qwen).
    *   **System Latency**: Czas potrzebny na przejście od planu do działającego kodu.
3.  **Reflective Feedback Loop**: Lab dostarcza "lekcje" do RAE-Memory, dzięki czemu system uczy się, który model najlepiej radzi sobie z konkretnym typem zadania.

## 📁 Struktura Danych
*   `/storage/experiments`: Surowe dane z każdego skanowania i operacji.
*   `/storage/insights`: Przetworzone raporty strategiczne.

---
**Module Status**: Active Research
**Goal**: Zero-Waste Autonomous Engineering
