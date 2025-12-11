# CODEx_PLAN.md — план работ для Codex

Репозиторий: `skillra_hse_pda`
Контекст:
- Учебный проект по курсу **«Python для анализа данных»** (ВШЭ).
- Продуктовый фундамент **Career & Job Market Navigator — Skillra**.

---

## 0. Контекст и ключевые файлы

### Данные и документация
- ТЗ курса: `docs/00_assignment_TZ.md`
- Продуктовый контекст Skillra: `docs/01_product_context_skillra.md`
- Словарь признаков hh‑датасета: `docs/02_feature_dictionary_hh.md`
- Сырой датасет вакансий: `data/raw/hh_moscow_it_2025_11_30.csv`

### Код и ноутбуки
- Основной ноутбук: `notebooks/01_hse_project.ipynb`
- Пакет: `src/skillra_pda/`:
  - `config.py` — пути и настройки,
  - `io.py` — I/O,
  - `cleaning.py` — предобработка,
  - `features.py` — признаки,
  - `eda.py` — табличные EDA‑агрегации,
  - `viz.py` — визуализации,
  - `market.py` — агрегированная витрина рынка,
  - `personas.py` — персоны и skill‑gap.
- Парсер данных hh.ru: `parser/hh_scraper.py` и сопутствующие файлы.
- Скрипты:
  - `scripts/run_pipeline.py` — основной пайплайн,
  - `scripts/validate_pipeline.py` — smoke‑тест пайплайна,
  - `scripts/validate_notebook.py` — проверка выполнения ноутбука.

---

## 1. Цели

### 1.1. Учебный проект (ВШЭ)
- Показать полный цикл анализа данных на Python:
  - от парсинга hh.ru до агрегированной витрины рынка;
  - от сырых данных до feature engineering и визуализаций.
- Отразить все этапы ТЗ (0–4) в `notebooks/01_hse_project.ipynb`:
  - Этап 0 — источник данных и парсер hh,
  - Этап 1 — предобработка,
  - Этап 2 — признаки,
  - Этап 3 — EDA (зарплаты, форматы, роли, навыки, английский, образование, домены, работодатели),
  - Этап 4 — визуализации и выводы.

### 1.2. Продукт Skillra
- Иметь фичевый датасет в `data/processed/`.
- Иметь `market_view.parquet` как агрегированное представление рынка.
- Иметь personas‑API:
  - `Persona` (цели, ограничения, текущие навыки),
  - `analyze_persona(df, persona)` → market summary + skill‑gap + рекомендации,
  - визуализацию gap’а (`plot_persona_skill_gap`).

---

## 2. Что уже готово (кратко)
- Пайплайн очистки и признаков реализован в `cleaning.py` и `features.py`.
- EDA и визуализации реализованы в `eda.py` и `viz.py`.
- Витрина рынка реализована в `market.py`.
- Персоны и gap‑анализ — в `personas.py`.
- `scripts/run_pipeline.py` и `scripts/validate_pipeline.py` работают.
- `notebooks/01_hse_project.ipynb` выполняется `Run All` и соответствует ТЗ.
- README описывает запуск пайплайна и ноутбука.
- Полезные идеи из `Group_project_draft.ipynb` интегрированы; сам ноутбук удалён.

---

## 3. Технический пайплайн
1. **Загрузка и предобработка**
   - `io.load_raw` → загрузка CSV.
   - `cleaning.handle_missingness`, `cleaning.parse_dates`, `cleaning.salary_prepare`, `cleaning.deduplicate` → чистый датасет.
   - Результат сохраняется в `data/processed/*clean*.parquet`.
2. **Признаки**
   - `features.assemble_features` добавляет city_tier, work_mode, домены, роли, стек, soft‑skills, бенефиты, английский, образование, salary buckets, vacancy_age_days и др.
   - Результат сохраняется в `data/processed/*features*.parquet`.
3. **Рынок и персоны**
   - `market.build_market_view(df_features)` → `market_view.parquet`.
   - `personas.analyze_persona(df_features, persona)` строит профиль спроса, считает skill‑gap и выдаёт рекомендации.

---

## 4. Ноутбук 01_hse_project.ipynb

Ноутбук — главный отчёт и витрина проекта. Внутри представлены:
- Вводная часть и связь с продуктом Skillra.
- Этап 0 — источник данных и устройство парсера hh.ru.
- Этап 1 — очистка, дубликаты, пропуски, обработка зарплат.
- Этап 2 — engineered‑признаки (city_tier, work_mode, роли, стек, английский, образование и др.).
- Этап 3 — EDA по зарплатам, форматам работы, ролям, навыкам, доменам, английскому, образованию, работодателям, корреляции.
- Этап 4 — визуализации, продуктовые выводы и слой персон с gap‑анализом.

---

## 5. Execution steps for Codex

Шаги выполняются **по одному**. Steps **0–10** уже завершены; открытые шаги: **Step 11** и **Step 12**.

### Step 0–10 — completed
- Базовый пайплайн (очистка, признаки, market_view) реализован и протестирован (`cleaning.py`, `features.py`, `market.py`).
- EDA и визуализации закрывают основные срезы рынка (`eda.py`, `viz.py`).
- Personas API работает и задокументирован (`personas.py`).
- Парсер hh.ru и скрипты пайплайна (`parser/`, `scripts/`) настроены; ноутбук `01_hse_project.ipynb` соответствует ТЗ.

### Step 11 — docs cleanup и стабилизация плана (open)
- **Файлы:** `AGENTS.md`, `CODEx_PLAN.md`, `README.md` (минимальные правки в секции установки и ссылки).
- **Задачи:**
  - зафиксировать статусы шагов (0–10 завершены, 11–12 открыты) и правила работы со steps;
  - убрать служебные артефакты и устаревшие ссылки, в т.ч. на `notebooks/Group_project_draft.ipynb`;
  - уточнить установку, включая `pip install -r requirements.txt` и parquet‑движок `pyarrow`.
- **Название PR:** `step11_docs_cleanup`.

### Step 12 — investor story and viz (open)
- **Файлы:** `notebooks/01_hse_project.ipynb`, `src/skillra_pda/eda.py`, `src/skillra_pda/viz.py`, `src/skillra_pda/personas.py`, `parser/hh_scraper.py`, `README.md`, `docs/01_product_context_skillra.md`.
- **Цель:** усилить ноутбук и продуктовую подачу.
- **Основные задачи:**
  1. Интегрировать неиспользованные функции EDA/Viz и `personas.plot_persona_skill_gap` в ноутбук с интерпретациями для рынка и продукта.
  2. Обеспечить отображение графиков (возврат фигур или вставка сохранённых изображений) без ломки API `eda`, `viz`, `personas`.
  3. Углубить сторителлинг (investor‑pitch + ТЗ): явные выводы и связь шагов с логикой продукта.
  4. Подробно описать парсер и масштаб данных; обновить README с инструкцией по запуску парсера и тестовому лимиту.
  5. Сделать каждый блок ноутбука прозрачным: пояснения к вызовам функций, выводы после таблиц/графиков.
- **Критерии готовности:** графики видны в ноутбуке; используются новые EDA/viz‑функции и persona‑график; README содержит секцию про парсер; пайплайн и тесты работают.
- **Название PR:** `step12_investor_story_and_viz`.
