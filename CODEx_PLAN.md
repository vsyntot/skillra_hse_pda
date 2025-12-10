# CODEx_PLAN.md — мастер‑план для `skillra_hse_pda`

Репозиторий: `skillra_hse_pda`  
Контекст:  
- Учебный проект по курсу **«Python для анализа данных»** (ВШЭ).  
- Продуктовый фундамент **Career & Job Market Navigator — Skillra**.

---

## 0. Контекст и ключевые файлы

### Данные и документация

- ТЗ курса: `docs/00_assignment_TZ.md`
- Продуктовый контекст Skillra: `docs/01_product_context_skillra.md`
- Словарь признаков hh-датасета: `docs/02_feature_dictionary_hh.md`
- Сырой датасет вакансий: `data/raw/hh_moscow_it_2025_11_30.csv`

### Код и ноутбуки

- Основной ноутбук: `notebooks/01_hse_project.ipynb`
- Черновой ноутбук команды: `notebooks/Group_project_draft.ipynb` (источник идей, не основной отчёт)
- Пакет: `src/skillra_pda/`
  - `cleaning.py` — предобработка
  - `features.py` — признаки
  - `eda.py` — EDA‑утилиты
  - `viz.py` — визуализации
  - `personas.py` — персоны и skill‑gap
  - `market.py` — (будет создан) агрегированная витрина рынка
  - `io.py`, `config.py` — I/O и пути
- Скрипты:
  - `scripts/validate_pipeline.py` — smoke‑тест
  - `scripts/run_pipeline.py` — (будет создан) основной пайплайн

---

## 1. Цели

### 1.1. Учебный проект (ВШЭ)

- Отразить все этапы ТЗ (0–4) в `01_hse_project.ipynb`.
- Дать чистый, воспроизводимый анализ:
  - загрузка и предобработка,
  - признаки,
  - EDA (зарплаты/форматы/роли/навыки/английский/образование/домены/работодатели),
  - визуализации,
  - финальные выводы.

### 1.2. Продуктовый фундамент Skillra

- Иметь фичевый датасет + `market_view.parquet` в `data/processed/`.
- Иметь personas‑API:
  - `Persona` (цели, ограничения, текущие навыки),
  - `analyze_persona(df, persona)` → market summary + skill‑gap + рекомендации.

---

## 2. Что считается «готово»

(Кратко, без деталей — выше мы уже обсуждали, поэтому здесь оставляем только резюме.)

- `01_hse_project.ipynb` выполняется **Run All**, красиво оформлен и закрывает ТЗ.
- В `data/processed/` есть:
  - чистый датасет,
  - фичевый датасет,
  - `market_view.parquet`.
- В `src/skillra_pda/personas.py` есть `analyze_persona`.
- В `docs/02_feature_dictionary_hh.md` отражены все ключевые признаки.

Подробная реализация разбита на шаги ниже.

---

## 6. Execution steps for Codex

**Важно для Codex:**  
Эти шаги выполняются **по одному**.  
Пользователь всегда говорит явно: «сделай Step N».  
Не пытайся выполнить все шаги одновременно.

Статус:  
- Steps 0–2 уже частично реализованы в текущей кодовой базе и ноутбуке.  
  Их сейчас можно использовать как **референс**, а не переписывать с нуля, если пользователь не попросит явно.

---

### Step 0 — Санити‑чек (без изменений кода)

**Цель:** убедиться, что окружение и структура репо нормальные.

**Действия для Codex:**

- Никаких изменений в коде.
- Проверить, что:
  - структура папок соответствует описанию,
  - `AGENTS.md` и этот `CODEx_PLAN.md` лежат в корне,
  - основная работа ведётся в `main` или соответствующей рабочей ветке.

**Ожидаемый PR:** нет (шаг без коммитов).

---

### Step 1 — Домены (domain_*) в EDA и ноутбуке

> ⚠️ В текущей базе этот шаг **частично уже сделан**.  
> Codex должен **не переписывать** существующий код, а:
> - либо ничего не делать, если всё уже реализовано,
> - либо аккуратно добавить недостающие куски.

**Разрешённые файлы:**

- `src/skillra_pda/eda.py`
- `src/skillra_pda/viz.py`
- `notebooks/01_hse_project.ipynb`
- при необходимости: `reports/figures/*` (только новые файлы)

**Цель:**

- Использовать `domain_*` признаки:
  - добавить функции:
    - `extract_primary_domain`,
    - `describe_salary_by_domain`,
  - добавить визуализацию `salary_by_domain_plot`,
  - добавить раздел в ноутбуке «Рынок по доменам».

**Название PR:** `step1_domain_eda`.

---

### Step 2 — Английский и образование

> ⚠️ Этот шаг также частично реализован.  
> Поведение такое же: не ломать уже рабочий код.

**Разрешённые файлы:**

- `src/skillra_pda/eda.py`
- `src/skillra_pda/viz.py`
- `notebooks/01_hse_project.ipynb`
- `reports/figures/*` (новые графики)

**Цель:**

- EDA по английскому:
  - функции `english_requirement_stats` + `salary_by_english_level_plot`,
  - раздел в ноутбуке с графиками и выводами.
- EDA по образованию:
  - функции `education_requirement_stats` + `salary_by_education_level_plot`,
  - раздел в ноутбуке с графиками и выводами.

**Название PR:** `step2_english_education_eda`.

---

### Step 3 — Работодатели, бенефиты и soft‑skills

**Разрешённые файлы:**

- `src/skillra_pda/eda.py`
- `src/skillra_pda/viz.py`
- `notebooks/01_hse_project.ipynb`
- `reports/figures/*` (новые png)

**Цель:**

- Добавить EDA по работодателям:
  - `top_employers`, `benefits_by_employer`, `soft_skills_by_employer` в `eda.py`,
  - `benefits_employer_heatmap`, `soft_skills_employer_heatmap` в `viz.py`.
- Добавить в ноутбуке секцию «Топ работодатели, бенефиты и soft‑skills»:
  - таблица топ работодателей,
  - 1–2 heatmap,
  - текстовые выводы.

**Ограничения:**

- Не изменять/не удалять существующие функции в `eda.py` и `viz.py`.
- В ноутбуке только добавлять новую секцию, не переписывая уже существующие.

**Название PR:** `step3_employers_benefits_softskills`.

---

### Step 4 — Personas & analyze_persona

**Разрешённые файлы:**

- `src/skillra_pda/personas.py`
- `notebooks/01_hse_project.ipynb`

**Цель:**

1. Расширить `Persona` (цели, ограничения, описание).
2. Реализовать high‑level функцию:

```python
   analyze_persona(df, persona, top_k=10) -> dict
```

со структурой: `market_summary`, `skill_gap`, `recommended_skills`.

3. Обновить секцию про персоны в ноутбуке:

   * для каждой персоны:

     * market summary,
     * табличка gap,
     * текстовые рекомендации.

**Название PR:** `step4_personas_analyze_persona`.

---

### Step 5 — Market view и run_pipeline

**Разрешённые файлы:**

* `src/skillra_pda/market.py` (новый файл)
* `scripts/run_pipeline.py` (новый или дописанный)
* при необходимости: `src/skillra_pda/__init__.py` (экспорт функций)
* `README.md` (обновить инструкцию по запуску пайплайна)

**Цель:**

1. Создать `build_market_view(df_features)` в `market.py`.
2. Реализовать `scripts/run_pipeline.py`:

   * загрузка raw,
   * cleaning,
   * feature engineering,
   * сохранение clean/features/market_view в `data/processed/`.

**Название PR:** `step5_market_view_pipeline`.

---

### Step 6 — Тесты и улучшение validate_pipeline

**Разрешённые файлы:**

* `tests/test_cleaning.py` (новый)
* `tests/test_features.py` (новый)
* `tests/test_personas.py` (новый)
* `scripts/validate_pipeline.py`
* `README.md` (раздел «Как проверить проект»)

**Цель:**

1. Добавить простые тесты для:

   * обработки `salary_gross`,
   * `add_city_tier`, `add_primary_role`,
   * `skill_gap_for_persona` / `build_skill_demand_profile`.
2. В `validate_pipeline.py`:

   * явно выводить ключевые метрики очистки (дубли, dropped_cols, non_RUB share).
3. В README:

   * добавить команды для `validate_pipeline` и `pytest`.

**Название PR:** `step6_tests_and_validation`.

---

### Step 7 — Документация и финальный полиш

**Разрешённые файлы:**

* `docs/02_feature_dictionary_hh.md`
* `docs/01_product_context_skillra.md` (при необходимости)
* `README.md`
* `notebooks/01_hse_project.ipynb`

**Цель:**

1. Обновить словарь признаков: добавить все engineered features.
2. В README/доках:

   * описать, как запускать пайплайн,
   * как использовать `market_view` и `analyze_persona` для Skillra.
3. В ноутбуке:

   * привести заголовки и нумерацию секций в порядок,
   * обновить финальный раздел с выводами, учитывая новые EDA.

**Название PR:** `step7_docs_and_polish`.

---

## 7. Правила для Codex при выполнении шагов

1. Каждый Step N — отдельная задача и отдельный PR.
2. При выполнении Step N:

   * не изменяй файлы, не перечисленные в этом шаге;
   * не переписывай уже реализованные функции без необходимости;
   * не выполняй другие Steps (N+1, N+2, …), пока пользователь явно не попросит.
3. Если код уже реализует то, что описано в шаге:

   * либо пропусти шаг,
   * либо сделай минимальные правки (например, дописать docstring или добавить выводы в ноут).

---