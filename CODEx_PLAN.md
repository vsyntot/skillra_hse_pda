# CODEx_PLAN.md — Skillra HSE Python for Data Analysis
Repo: skillra_hse_pda
Goal: выполнить проект по Python для анализа данных (этапы 0–4) + дать продуктовый слой для Skillra (Career & Job Market Navigator).

---

## 0) ВАЖНО: что считать “готово”
### Обязательные артефакты (для сдачи в ВШЭ)
1) `notebooks/01_hse_project.ipynb` — финальный ноутбук, который выполняется **Run All** без ошибок.
2) Данные (минимум сырой CSV) в репозитории: `data/raw/*.csv`.
3) Внутри ноутбука:
   - заголовки/подзаголовки Markdown,
   - промежуточные выводы (не «голый код»),
   - в самом начале — список вкладов участников (можно placeholders),
   - выполнены этапы 0–4 (парсинг описан, предобработка, фичи, EDA, визуализация).
4) Экспортированные графики в `reports/figures/` (png или svg).

### Дополнительно (очень желательно)
- `README.md` с инструкцией “как запустить”.
- `requirements.txt` для воспроизводимости.
- `data/processed/` (parquet/csv) — чистый датасет и агрегаты для графиков.

---

## 1) ВХОДНЫЕ ДАННЫЕ И ДОКИ (что читать первым)
Перед началом работы прочитать и использовать как спецификацию:
- `docs/00_assignment_TZ.md` — требования курса (этапы/критерии).
- `docs/01_product_context_skillra.md` — цели MVP Skillra.
- `docs/02_feature_dictionary_hh.md` — словарь признаков датасета.
- `data/raw/hh_moscow_it_2025_11_30.csv` — основной датасет (7026×151, много булевых фич).

Не менять “сырой” CSV. Все преобразования — в `data/processed/`.

---

## 2) ПРАВИЛА РАБОТЫ В РЕПО
- Никаких секретов/токенов в репо. Если в `parser/` есть конфиги — убедиться, что там нет приватных данных.
- Использовать только относительные пути (через `pathlib.Path`).
- Графики сохранять в `reports/figures/` с фиксированными именами (см. раздел 7).
- В ноутбуке избегать чрезмерной магии: лучше функции в `src/skillra_pda/`, ноутбук — как отчёт.

---

## 3) ТЕХНИЧЕСКИЙ СЕТАП
### 3.1. Зависимости
Создать/обновить `requirements.txt` (минимум):
- pandas
- numpy
- matplotlib
- scipy (опционально, для статистики)
- scikit-learn (опционально, для кластеризации как “бонус”)
- pyarrow (если сохраняем parquet)

### 3.2. Пакет проекта
Убедиться, что существует пакет:
`src/skillra_pda/__init__.py`

Добавить модули:
- `src/skillra_pda/config.py`
- `src/skillra_pda/io.py`
- `src/skillra_pda/cleaning.py`
- `src/skillra_pda/features.py`
- `src/skillra_pda/eda.py`
- `src/skillra_pda/viz.py`
- `src/skillra_pda/personas.py`

---

## 4) DATA LOADING + VALIDATION (Этап 1 начинается тут)
### 4.1. io.py
Реализовать:
- `load_raw(path: Path) -> pd.DataFrame`
  - `low_memory=False`
  - нормализация названий колонок не нужна (используем как есть)
- `save_processed(df, path: Path)`

### 4.2. Быстрая валидация
В `cleaning.py` реализовать:
- `basic_profile(df) -> dict` (shape, dtypes summary, missing top-20)
- `check_unique_id(df, id_col="vacancy_id")`
- `detect_column_groups(df) -> dict`:
  - prefixes: `has_`, `skill_`, `benefit_`, `soft_`, `domain_`, `role_`
  - возвращает списки колонок по каждой группе

В ноутбуке показать:
- `df.shape`
- `df.head(3)`
- список групп колонок и их размерности
- топ пропусков

---

## 5) ПРЕДОБРАБОТКА (Этап 1)
### 5.1. Цели предобработки
- привести типы (даты → datetime; булевы → bool/Int8; категории → category),
- обработать пропуски,
- обработать дубликаты (если есть),
- обработать выбросы,
- подготовить зарплату для анализа (важно: мультивалюта).

### 5.2. cleaning.py — функции
Реализовать:
- `parse_dates(df)`: `published_at_iso`, `scraped_at_utc` → datetime (errors="coerce")
- `handle_missingness(df, drop_threshold=0.95)`:
  - столбцы с долей NaN >= threshold → drop (с логом списка)
  - категориальные NaN → "unknown"
  - текстовые NaN → ""
- `salary_prepare(df)`:
  - создать `salary_mid_rub`:
    - если currency == "RUB" → salary_mid
    - иначе NaN (по умолчанию)
  - создать `salary_known` (bool)
  - сделать обрезку выбросов на RUB (winsorize по 1–99 перцентилям) → `salary_mid_rub_capped`
  - посчитать долю не-RUB и вывести отдельно как “важное ограничение”
- `deduplicate(df)`:
  - если вдруг есть дубль по `vacancy_id`, оставить самый свежий `scraped_at_utc` (или первый)

**Результат:** `df_clean` и сохранение в `data/processed/hh_clean.parquet` (или csv).

---

## 6) FEATURE ENGINEERING (Этап 2)
### 6.1. Новые признаки (создать минимум 2, лучше 6–10)
В `features.py` реализовать:

1) Временные фичи (из `published_at_iso`):
- `published_weekday` (0–6)
- `published_month` (1–12)
- `is_weekend_post` (bool)

2) Гео-уровень:
- `city_tier` (категория):
  - "Moscow"
  - "SPb"
  - "Million+"
  - "Other RU"
  - "KZ/Other"
  (если в датасете встречаются KZ города — отнести туда)

3) Формат работы:
- `work_mode` ∈ {"remote","hybrid","office","unknown"}
  - приоритет: is_remote → remote; else is_hybrid → hybrid; else work_format == office → office

4) Индексы:
- `benefits_count` = сумма `benefit_*` (True=1)
- `soft_skills_count` = сумма `soft_*`
- `hard_stack_count` = сумма `has_*` и/или `skill_*` (по группам)
- `role_count` = сумма `role_*`

5) Primary role (сжатие роли в 1 категорию):
- `primary_role` (category), правило приоритета (пример):
  1) role_ml
  2) role_data
  3) role_devops
  4) role_backend
  5) role_frontend
  6) role_fullstack
  7) role_mobile
  8) role_qa
  9) role_product
  10) role_manager
  11) role_analyst
  12) "other"

6) Зарплатные бины:
- `salary_bucket` — квантильные группы по `salary_mid_rub_capped` (например, low/mid/high)

**Результат:** `df_features`, сохранение в `data/processed/hh_features.parquet`.

---

## 7) EDA (Этап 3) — “Карта рынка” под Skillra
### 7.1. Блоки анализа (обязательные выводы в markdown)
В `eda.py` реализовать функции, а в ноутбуке — результаты и интерпретации.

A) Снимок рынка
- распределение вакансий по:
  - `primary_role`
  - `grade`
  - `city_tier`
  - `work_mode`
- “junior-friendly” (если есть колонки):
  - `is_for_juniors`, `allows_students`, `has_mentoring`, `has_test_task`

B) Зарплаты (только `salary_mid_rub_capped` != NaN)
- медиана/квантили зарплат по:
  - `grade × primary_role`
  - `work_mode × primary_role`
  - `city_tier × grade`
- сравнить домены (если есть `domain_*`):
  - медиана зарплат по доменам и роль/грейд (минимум 1–2 разреза)

C) Skills demand (частоты)
- топ-15 `has_*` и `skill_*`:
  - отдельно для `primary_role` in {"data","ml","devops"} (если есть)
- доли навыков по грейдам (heatmap подготовить таблицей)

D) Skill premium (связь “навык → зарплата”)
- для 10–20 ключевых навыков:
  - сравнить медиану `salary_mid_rub_capped` у вакансий с навыком vs без
  - вывести таблицу “premium_abs / premium_pct / count_with_skill”

E) Текст как прокси сложности (если есть текстовые и счетчики)
- связь `salary_mid_rub_capped` с:
  - `must_have_skills_count`, `requirements_count`
  - `tech_stack_size` или `hard_stack_count`
  - `description_len_words`

F) Корреляции
- собрать числовые признаки (15–25 штук) и построить корр-матрицу
- вывести 3–5 наблюдений (не “корреляция не равна причинности”, а реально что видно в данных)

---

## 8) ВИЗУАЛИЗАЦИИ (Этап 4)
В `viz.py` сделать функции, которые:
- строят график,
- подписывают оси/заголовок,
- сохраняют в `reports/figures/*.png`.

Минимум 3 разных типа графиков. Сделать 6 (чтобы было что вставить в презентацию):

1) `fig_salary_by_grade_box.png`
- boxplot/violin: `salary_mid_rub_capped` по `grade`

2) `fig_salary_by_role_box.png`
- boxplot/violin: зарплаты по `primary_role` (ограничить топ-8 по частоте)

3) `fig_work_mode_share_by_city.png`
- stacked bar: доля `work_mode` по `city_tier`

4) `fig_top_skills_data_bar.png`
- bar: топ-15 навыков для роли data (частоты)

5) `fig_skill_premium_bar.png`
- bar: top-10 “skill premium” (pct) среди навыков с достаточным n

6) `fig_corr_heatmap.png`
- heatmap: корреляционная матрица выбранных числовых признаков

Все графики должны иметь читабельные подписи и быть пригодны “в слайд”.

---

## 9) ПРОДУКТОВЫЙ СЛОЙ (Skillra Navigator) — как “плюс-балл”
Цель: не просто EDA, а 2–3 сценария “как помочь человеку”.

В `personas.py` реализовать:
- структура “персона”:
  - имя (заглушка)
  - current_skills (список)
  - target_role, target_grade
  - constraints (remote_only, city_tier и т.п.)

Реализовать функцию:
- `skill_gap_for_persona(df_features, persona, top_k=10)`:
  - найти вакансии под persona (фильтры по role/grade/work_mode)
  - посчитать топ-k навыков (из has_/skill_ групп)
  - вернуть таблицу:
    - skill
    - market_share (доля вакансий)
    - persona_has (0/1)
    - gap (1 если не хватает)

В ноутбуке сделать 2–3 персоны:
1) “магистрант по данным → Junior DA/DS”
2) “свитчер → BI/продуктовый аналитик”
3) “аналитик → middle data analyst”

И под каждую:
- табличка gap
- 2–3 вывода “что учить/куда целиться” на основе рынка

---

## 10) НОУТБУК: что Codex должен создать/дописать
Файл: `notebooks/01_hse_project.ipynb`

Codex сам делает оглавление, но обязательно разложить по разделам:

0. Title + “вклад участников” (placeholders) + что за датасет (источник/период/как собирали)
1. Загрузка данных
2. Паспорт датасета и качество
3. Предобработка (пропуски/дубликаты/выбросы/зарплата/валюта)
4. Новые признаки
5. EDA блоки A–F
6. Визуализации (с сохранением файлов)
7. Product: персоны и skill-gap
8. Итоговые выводы (коротко, пунктами)
9. Чек-лист соответствия требованиям курса

Обязательное правило: после каждого большого блока — markdown “что увидели / что это значит”.

---

## 11) QA / “Run All” чек-лист
Перед завершением:
- ноутбук выполняется с нуля без ручных вмешательств
- пути к данным работают из корня репо
- сохранены все 6 графиков в `reports/figures/`
- сохранены `data/processed/hh_clean.*` и `hh_features.*` (если папка не игнорируется)
- в начале ноутбука есть список вкладов участников
- минимум 2 новых признака реально созданы (а не только уже существующие)

---

## 12) НЕ-ЦЕЛИ (чтобы не утонуть)
- не строить “идеальную” ML-модель предсказания зарплаты (можно как бонус, но только после закрытия ТЗ)
- не рефакторить парсер
- не делать веб-интерфейс

---

## 13) ПОРЯДОК КОММИТОВ (чтобы было удобно ревьюить)
1) deps + scaffold (`requirements.txt`, `src/skillra_pda/*` пустые)
2) data pipeline (load/clean/features/save)
3) notebook skeleton + EDA tables
4) visualizations + экспорт
5) personas + skill gap + финальные выводы
6) README polish

Done.
