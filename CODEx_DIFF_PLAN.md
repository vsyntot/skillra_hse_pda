# CODEx_DIFF_PLAN.md — финальный апгрейд Skillra HSE PDA

Repo: `vsyntot/skillra_hse_pda`  

Контекст:
- ТЗ курса «Python для анализа данных» (этапы 0–4, структура ноутбука, визуализации, текстовые выводы).
- Продуктовый план **Career & Job Market Navigator — Skillra** (MVP до конца семестра).
- Словарь признаков hh-датасета Skillra и наработки командного ноутбука по EDA.

Цели этого плана:

1. Довести кодовую базу до устойчивого, читабельного состояния (архитектура модулей, типы, сохранение данных).
2. Максимально закрыть ТЗ курса по Python (этапы 0–4 + аккуратное оформление ноутбука, дополнительные баллы за глубину).
3. Интегрировать полезные идеи из командного ноутбука (кластер навыков, EDA по навыкам/бенефитам/soft skills, распределения).
4. Укрепить продуктовый слой Skillra: карта рынка, skill‑premium, персоны и skill‑gap, связка с карьерными сценариями.
5. Обеспечить техническую возможность быстро проверить пайплайн и ноутбук (скрипты запуска и валидации).

---

## 0. Общие правила для изменений

- Не изменять файлы в `data/raw/*`.
- Использовать только относительные пути через `src/skillra_pda/config.py`.
- Новая логика — в:
  - `src/skillra_pda/cleaning.py`
  - `src/skillra_pda/io.py`
  - `src/skillra_pda/features.py`
  - `src/skillra_pda/eda.py`
  - `src/skillra_pda/viz.py`
  - `src/skillra_pda/personas.py`
  - `scripts/run_pipeline.py`
  - `scripts/validate_notebook.py`
  - `notebooks/01_hse_project.ipynb`
  - `README.md`
- Соблюдать единый стиль:
  - функции верхнего уровня, без тяжёлой логики в ноутбуке;
  - по возможности type hints;
  - минимум «магических констант» без комментариев.
- Коммиты — небольшие и осмысленные (cleaning → io → features → eda/viz → personas → scripts → notebook → README).

---

## 1. `cleaning.py` — прозрачная и устойчивая предобработка

**Файл:** `src/skillra_pda/cleaning.py`  

Предобработка должна чётко покрывать требования этапа 1 ТЗ (пропуски, дубликаты, выбросы, объяснение решений) и при этом не ломаться на булевых колонках и parquet.

### 1.1. Разбить `handle_missingness` на подфункции

**Задача:**

1. Вынести логику в приватные функции:

```python
def _drop_mostly_missing_columns(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame: ...
def _coerce_boolean_like_columns(df: pd.DataFrame) -> pd.DataFrame: ...
def _fill_categorical_missing(df: pd.DataFrame) -> pd.DataFrame: ...
def _fill_numeric_missing(df: pd.DataFrame) -> pd.DataFrame: ...
```

2. Переписать `handle_missingness` так:

```python
def handle_missingness(df: pd.DataFrame, drop_threshold: float = 0.95) -> pd.DataFrame:
    df = df.copy()
    df = _drop_mostly_missing_columns(df, threshold=drop_threshold)
    df = _coerce_boolean_like_columns(df)
    df = _fill_categorical_missing(df)
    df = _fill_numeric_missing(df)
    return df
```

3. В `df.attrs` сохранять служебную информацию:

- `dropped_cols` — список дропнутых колонок;
- `bool_like_cols` — какие колонки приведены к boolean;
- `filled_categorical_cols` — в каких категориальных заполнили пропуски;
- `filled_numeric_cols` — в каких числовых заполнили пропуски.

### 1.2. Убедиться, что все булевые признаки — нормальные `boolean`, без `"unknown"`

Ключевой кейс: `salary_gross` и все `is_*`, `has_*`, `benefit_*`, `soft_*`, `domain_*`, `role_*` должны храниться как `pandas.BooleanDtype` (nullable), без строковых `"unknown"`. Это важно и для корректного parquet, и для логики признаков в продукте.

**Сделать:**

1. В `_coerce_boolean_like_columns`:

   - Определить множества:

```python
BOOL_STR_VALUES = {"true", "false", "yes", "no", "1", "0",
                   "unknown", "", "n/a", "nan"}
```

   - Для object‑колонок, у которых множество уникальных значений (без NaN) входит в `BOOL_STR_VALUES ∪ {True, False, 0, 1}`:

     - заменить `"unknown", "", "n/a", "nan"` → `pd.NA`;
     - `"true","yes","1"` → `True`;
     - `"false","no","0"` → `False`;
     - привести к `astype("boolean")`.

2. Отдельно обработать `salary_gross`:

```python
if "salary_gross" in df.columns:
    df["salary_gross"] = (
        df["salary_gross"]
        .astype(str).str.lower()
        .replace({"unknown": None, "": None, "nan": None, "n/a": None})
        .map({"true": True, "false": False, "1": True, "0": False})
        .astype("boolean")
    )
```

3. При возможности, пройтись по всем колонкам с префиксами `["is_", "has_", "benefit_", "soft_", "domain_", "role_"]` и привести их к `boolean`, используя аналогичную логику.

### 1.3. Добавить/подтвердить `vacancy_age_days` в `parse_dates`

**Задача:**

- В `parse_dates` после нормализации `published_at_iso` и `scraped_at_utc` добавить:

```python
if "published_at_iso" in df.columns and "scraped_at_utc" in df.columns:
    df["vacancy_age_days"] = (
        df["scraped_at_utc"] - df["published_at_iso"]
    ).dt.days
```

**Зачем:**  
Этот признак важен для анализа «свежести» и динамики вакансий, и он явно фигурирует в словаре признаков и продуктовом плане.

---

## 2. `io.py` — безопасное сохранение (особенно parquet)

**Файл:** `src/skillra_pda/io.py`  

### 2.1. Parquet-safe хелпер

**Задача:**

1. Добавить приватную функцию:

```python
def _coerce_boollike_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    BOOL_LIKE_VALUES = {...}   # как в cleaning
    REPLACE_MAP = {...}        # строки -> bool / pd.NA
    for col in df.columns:
        if df[col].dtype == "object":
            vals = set(df[col].dropna().unique())
            if vals and vals.issubset(BOOL_LIKE_VALUES):
                df[col] = df[col].replace(REPLACE_MAP).astype("boolean")
        elif df[col].dtype == bool:
            df[col] = df[col].astype("boolean")
    return df
```

2. В `save_processed` перед `to_parquet`:

```python
if output_path.suffix.lower() == ".parquet":
    df_out = _coerce_boollike_object_columns(df)
    df_out.to_parquet(output_path, index=False)
else:
    df.to_csv(output_path, index=False)
```

---

## 3. `features.py` — новые фичи и выравнивание со словарём

**Файл:** `src/skillra_pda/features.py`  

Фичи должны логически продолжать архитектуру признаков из словаря Skillra (зарплата, geo, формат, опыт, роли, стек, soft, domain и т.п.).

### 3.1. Flags «junior-friendly» и «боевой опыт» (battle_experience)

**Задача:**

1. Добавить функцию:

```python
def add_experience_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = set(df.columns)

    if {"is_for_juniors", "allows_students", "exp_is_no_experience"} <= cols:
        df["is_junior_friendly"] = (
            df["is_for_juniors"].fillna(False)
            | df["allows_students"].fillna(False)
            | df["exp_is_no_experience"].fillna(False)
        ).astype("boolean")

    if "is_junior_friendly" in df.columns:
        df["battle_experience"] = (~df["is_junior_friendly"]).astype("boolean")

    return df
```

2. Включить `add_experience_flags` в `engineer_all_features`.

### 3.2. Уточнить `city_tier` и `work_mode`

**Задача:**

1. В `_city_to_tier` добавить мэппинг русских названий миллионников:

- `"Новосибирск"`, `"Екатеринбург"`, `"Казань"`, `"Нижний Новгород"`, `"Челябинск"`, `"Самара"`, `"Ростов-на-Дону"`, `"Уфа"`, `"Красноярск"` → `"Million+"`.

2. В `add_work_mode`:

   - Если `work_format` уже в нормализованных значениях (`"office"`, `"remote"`, `"hybrid"`, `"field"`) — использовать его как источник правды.
   - Только если `work_format` пуст/неизвестен, работать через `is_remote`/`is_hybrid`.

### 3.3. Агрегаты по стеку: `core_data_skills_count`, `ml_stack_count`, `tech_stack_size`

**Задача:**

1. В начале файла объявить:

```python
CORE_DATA_SKILLS = [
    "skill_sql", "skill_excel", "skill_powerbi", "skill_tableau",
    "skill_clickhouse", "skill_bigquery", "has_python", "skill_r"
]

ML_STACK_SKILLS = [
    "has_sklearn", "has_pytorch", "has_tensorflow",
    "has_airflow", "has_spark", "has_kafka"
]
```

2. Добавить функцию:

```python
def add_stack_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bool_like = df.select_dtypes(include=["boolean", "bool", "object"])

    df["core_data_skills_count"] = (
        bool_like.reindex(columns=CORE_DATA_SKILLS, fill_value=False)
        .fillna(False).astype(int).sum(axis=1)
    )

    df["ml_stack_count"] = (
        bool_like.reindex(columns=ML_STACK_SKILLS, fill_value=False)
        .fillna(False).astype(int).sum(axis=1)
    )

    tech_cols = [c for c in df.columns if c.startswith("has_") or c.startswith("skill_")]
    df["tech_stack_size"] = (
        bool_like.reindex(columns=tech_cols, fill_value=False)
        .fillna(False).astype(int).sum(axis=1)
    )

    return df
```

3. Включить `add_stack_aggregates` в `engineer_all_features`.

### 3.4. Текстовые фичи — таргетно по описанию

**Задача:**

1. Переписать `add_text_features` так, чтобы он работал только по ключевым колонкам (например, `description`):

```python
def add_text_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "description" in df.columns:
        desc = df["description"].fillna("")
        df["description_len_chars"] = desc.str.len()
        df["description_len_words"] = desc.str.split().str.len()
    return df
```

2. Если в датасете есть разметка секций («Обязанности», «Требования», «Будет плюсом» и т.п.), убедиться, что рассчитанные счётчики (`requirements_count`, `responsibilities_count`, `must_have_skills_count`, `optional_skills_count`) попадают в итоговый features‑датасет.

### 3.5. `compute_skill_premium` — корректная работа с nullable‑bool

**Задача:**

- В `compute_skill_premium` заменить сравнение `df[col] == 1` на работу с булевыми колонками:

```python
has_skill = df[col].fillna(False).astype(bool)
no_skill = ~has_skill
```

- Остальная логика (агрегаты, премии, сортировка) остаётся прежней.

---

## 4. `eda.py` — high-level EDA по паттернам из командного ноутбука

**Файл:** `src/skillra_pda/eda.py`  

Задача — оформить EDA‑паттерны (разрезы зарплат, skills vs grade, бенефиты, soft skills, junior‑friendly) как функции, чтобы ноутбук был чистым сценарием.

### 4.1. Salary by category

Добавить функции:

```python
def salary_summary_by_category(
    df: pd.DataFrame,
    category_col: str,
    salary_col: str = "salary_mid_rub_capped"
) -> pd.DataFrame:
    # Возвращает аггрегацию по salary_col:
    # count, mean, median, std, min, max для каждой категории.
    ...

def salary_by_city_tier(df: pd.DataFrame) -> pd.DataFrame: ...
def salary_by_grade(df: pd.DataFrame) -> pd.DataFrame: ...
def salary_by_primary_role(df: pd.DataFrame) -> pd.DataFrame: ...
def salary_by_experience_bucket(df: pd.DataFrame) -> pd.DataFrame: ...
def salary_by_english_level(df: pd.DataFrame) -> pd.DataFrame: ...
def salary_by_stack_size(df: pd.DataFrame) -> pd.DataFrame: ...
```

Где:

- `experience_bucket` строится из `exp_min_years` / `exp_max_years` (0–1, 1–3, 3–6, 6+);
- `stack_size` — биннинг по `tech_stack_size` (например, `[0–2, 3–5, 6–8, 9+]`).

### 4.2. Skills × grade heatmap

Добавить:

```python
def skill_share_by_grade(
    df: pd.DataFrame,
    skill_cols: list[str],
    grade_col: str = "grade"
) -> pd.DataFrame:
    # Возвращает DataFrame с index=skill, columns=grade,
    # values = доля вакансий с этим скиллом внутри грейда.
    ...
```

Использовать список из топ‑N boolean‑skills (`has_*/skill_*`), отобранных по сумме True.

### 4.3. Benefits и soft skills

Добавить:

```python
def benefits_summary_by_company(
    df: pd.DataFrame,
    company_col: str = "company",
    top_n: int = 10
) -> pd.DataFrame: ...

def benefits_summary_by_grade(df: pd.DataFrame) -> pd.DataFrame: ...

def soft_skills_overall_stats(df: pd.DataFrame) -> pd.DataFrame: ...

def soft_skills_by_employer(
    df: pd.DataFrame,
    company_col: str = "company",
    top_n: int = 10
) -> pd.DataFrame: ...

def soft_skills_correlation(df: pd.DataFrame) -> pd.DataFrame: ...
```

### 4.4. Junior‑friendly share и battle_experience

Добавить:

```python
def junior_friendly_share(
    df: pd.DataFrame,
    group_col: str = "primary_role"
) -> pd.DataFrame:
    # Доля junior-friendly вакансий и battle_experience в разрезе group_col.
    # Ожидает наличие is_junior_friendly и battle_experience в df.
```

---

## 5. `viz.py` — витринные графики

**Файл:** `src/skillra_pda/viz.py`  

### 5.1. Salary mean + count bar

Добавить:

```python
def salary_mean_and_count_bar(
    df: pd.DataFrame,
    category_col: str,
    salary_col: str = "salary_mid_rub_capped",
    top_n: int = 10,
    figsize=(10, 6),
    output_path: Path | None = None
) -> None:
    # Строит барпоинт по средней или медианной зарплате
    # и числу вакансий для top_n категорий.
```

### 5.2. Heatmap’ы

Добавить:

```python
def heatmap_skills_by_grade(
    skill_share: pd.DataFrame,
    figsize=(10, 6),
    output_path: Path | None = None
) -> None: ...

def heatmap_benefits_by_company(
    benefits_df: pd.DataFrame,
    figsize=(10, 6),
    output_path: Path | None = None
) -> None: ...

def heatmap_soft_skills_correlation(
    corr_df: pd.DataFrame,
    figsize=(8, 6),
    output_path: Path | None = None
) -> None: ...
```

### 5.3. Distribution + boxplot helper

Добавить:

```python
def distribution_with_boxplot(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
    figsize=(10, 6),
    output_path: Path | None = None
) -> None:
    # Гистограмма + boxplot для числовой фичи
    # (например, salary_mid_rub_capped, tech_stack_size, vacancy_age_days).
```

### 5.4. Валидация входных колонок

Во всех публичных функциях `viz.py`:

- В начале проверять наличие нужных колонок и при их отсутствии поднимать `ValueError` с понятным сообщением.

---

## 6. `personas.py` — продуктовый слой (персоны и skill‑gap)

**Файл:** `src/skillra_pda/personas.py`  

### 6.1. Dataclass Persona и фильтры

Переписать структуру персоны:

```python
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Persona:
    name: str
    description: str
    current_skills: List[str]    # имена колонок has_*/skill_*
    target_filter: Dict[str, str]  # grade, primary_role, work_mode, city_tier и т.п.
```

### 6.2. `skill_gap_for_persona`

Переписать/доработать:

```python
def skill_gap_for_persona(
    df: pd.DataFrame,
    persona: Persona,
    skill_cols: List[str],
    min_share: float = 0.1
) -> pd.DataFrame:
    # 1) Фильтрует df по persona.target_filter.
    # 2) Считает долю вакансий с каждым skill_col.
    # 3) Возвращает DataFrame со столбцами:
    #    - skill_name
    #    - market_share
    #    - persona_has (0/1)
    #    - gap (True, если persona_has == 0 и market_share >= min_share)
```

---

## 7. `scripts` — быстрый запуск и валидация ноутбука

### 7.1. `scripts/run_pipeline.py`

**Цель:** один вход для подготовки данных: raw → clean → features.

Пример:

```python
from skillra_pda import config, io, cleaning, features

def main() -> None:
    df_raw = io.load_raw(config.RAW_DATA_FILE)
    df_clean = cleaning.handle_missingness(df_raw)
    df_clean = cleaning.parse_dates(df_clean)
    df_clean = cleaning.salary_prepare(df_clean)
    df_clean = cleaning.deduplicate(df_clean)
    io.save_processed(df_clean, config.CLEAN_DATA_FILE)

    df_features = features.engineer_all_features(df_clean)
    io.save_processed(df_features, config.FEATURES_DATA_FILE)

if __name__ == "__main__":
    main()
```

### 7.2. `scripts/validate_notebook.py`

**Цель:** быстрая проверка, что `01_hse_project.ipynb` выполняется end‑to‑end.

Пример (через `jupyter nbconvert`):

```python
import subprocess
from pathlib import Path

NOTEBOOK = Path("notebooks/01_hse_project.ipynb")

def main() -> None:
    subprocess.run(
        [
            "jupyter", "nbconvert",
            "--to", "html",
            "--execute",
            "--ExecutePreprocessor.timeout=600",
            str(NOTEBOOK),
        ],
        check=True,
    )

if __name__ == "__main__":
    main()
```

---

## 8. `01_hse_project.ipynb` — структура и оформление

**Файл:** `notebooks/01_hse_project.ipynb`  

Ноутбук должен:

- чётко следовать этапам 0–4 ТЗ;
- содержать вклад участников;
- иметь заголовки/подзаголовки Markdown;
- иметь осмысленные текстовые выводы после каждого блока;
- использовать функции из `src/skillra_pda`, а не писать тяжёлую логику inline.

### 8.1. Предлагаемая структура разделов

0. **Обложка и команда**  
   - Название проекта.  
   - 2–3 предложения: откуда датасет, зачем его анализируем.  
   - Таблица «участник → вклад» (по требованиям ТЗ).  

1. **Этап 0. Данные и парсинг**  
   - Краткое описание: источник данных (hh.ru), как собирали (парсер).  
   - `df_raw.shape`, первые строки, список ключевых колонок.  
   - Ссылка на словарь признаков Skillra как на спецификацию признаков.  

2. **Этап 1. Предобработка**  
   - Вызов `basic_profile`, вывод missing’ов.  
   - Вызов `handle_missingness`, вывод `df.attrs["dropped_cols"]` и других атрибутов.  
   - Вызов `parse_dates`, `salary_prepare`, `deduplicate`.  
   - Сравнение формы/качеств до/после.  
   - Markdown‑выводы: что дропнули, чем и почему заполнили, как обрабатывали выбросы по зарплате.

3. **Этап 2. Новые признаки**  
   - Вызов `engineer_all_features`.  
   - Краткий словарь ключевых фич:
     - `city_tier`, `work_mode`, `vacancy_age_days`,
     - `core_data_skills_count`, `ml_stack_count`, `tech_stack_size`,
     - `description_len_chars`, `salary_bucket`,
     - `is_junior_friendly`, `battle_experience`,
     - `primary_role`, `benefits_count`, `soft_skills_count`.  
   - 1–2 таблицы/describe по новым признакам.

4. **Этап 3. EDA**  

Подразделы:

- 3.1 Зарплаты:
  - по `city_tier`, `grade`, `primary_role`, `experience_bucket`, `lang_english_level`, `tech_stack_size` (через функции `eda.salary_*`).  
- 3.2 Навыки × грейды:
  - получение `skill_share_by_grade`,
  - подготовка данных для heatmap,
  - текстовый вывод: как меняется стек от junior к senior.  
- 3.3 Бенефиты:
  - анализ `benefits_summary_by_company` / `benefits_summary_by_grade`.  
- 3.4 Soft skills:
  - `soft_skills_overall_stats`, `soft_skills_correlation`.  
- 3.5 Junior-friendly / battle_experience:
  - `junior_friendly_share` по ролям/грейдам.

Закончить блоком с 5–7 bullet‑инсайтами.

5. **Этап 4. Визуализация**  

Выбрать и построить 5–6 графиков (из `viz.py`):

- boxplot зарплат по `grade`;
- boxplot зарплат по `primary_role`;
- `salary_mean_and_count_bar` по `grade` или `primary_role`;
- stacked bar `work_mode_share_by_city`;
- `heatmap_skills_by_grade`;
- `heatmap_soft_skills_correlation` или heatmap бенефитов.

Под каждым графиком — краткий текст (2–3 предложения), что видно и почему это важно.

6. **Персоны и skill‑gap**  

- Завести 2–3 персоны (например: магистр по данным → junior DA/DS; свитчер → BI/продуктовый аналитик; аналитик → middle DA).  
- Для каждой:
  - задать `Persona` в коде;
  - получить `skill_gap_for_persona`;
  - показать таблицу топ‑gap навыков;
  - построить график skill‑gap (barplot).  
- Текстовые выводы: что именно не хватает персоне, какие шаги нужны.

7. **Итоговые выводы и связь с продуктом Skillra**  

- 5–7 bullets:
  - что мы узнали о рынке (зарплаты, навыки, бенефиты);
  - как это ложится в продуктовый сценарий Career & Job Market Navigator (карта рынка, рекомендации, AI‑агент).  

8. **Чек‑лист соответствия ТЗ**  

- Табличка по этапам 0–4 + «доп. балл» (что сделали и где в ноутбуке).

### 8.2. Технические требования к ноутбуку

- Ноутбук должен выполняться через `Restart Kernel & Run All` после запуска `python scripts/run_pipeline.py`.
- Все пути к данным использовать через `config`, не хардкодить относительные пути.
- Не дублировать тяжёлый код из `src/skillra_pda` — только вызовы функций.

---

## 9. `README.md` — связка Python‑проекта и продукта Skillra

**Файл:** `README.md`  

Добавить/обновить секции:

1. **О проекте**  
   - 2–3 абзаца: что такое Skillra Career & Job Market Navigator, что делает этот Python‑проект.

2. **Стек и установка**  
   - `pip install -r requirements.txt`
   - требования к версии Python.

3. **Запуск**  
   - `python scripts/run_pipeline.py` — подготовка данных (raw → clean → features).  
   - `python scripts/validate_notebook.py` — проверка выполнения ноутбука.

4. **Артефакты**  
   - `data/processed/hh_clean.parquet`, `hh_features.parquet`;  
   - `notebooks/01_hse_project.ipynb` — основной отчёт;  
   - `reports/figures/*` — графики для презентаций.

5. **Соответствие ТЗ курса**  
   - Пунктами: как проект покрывает этапы 0–4 и доп. балл за оформление.

6. **Связь с продуктом**  
   - Как Python‑часть используется для:
     - карты рынка,
     - анализа навыков,
     - построения карьерных сценариев и персон.

---

## 10. Definition of Done

Считаем план выполненным, когда:

1. **Кодовая база**
   - Все изменения в `cleaning.py`, `io.py`, `features.py`, `eda.py`, `viz.py`, `personas.py`, `scripts/*` реализованы.
   - Булевые колонки (`salary_gross`, `is_*`, `has_*`, `benefit_*`, `soft_*`, `domain_*`, `role_*`) имеют тип `boolean` без строковых `unknown`.
   - `python scripts/run_pipeline.py` и `python scripts/validate_notebook.py` отрабатывают без ошибок.

2. **Ноутбук**
   - `notebooks/01_hse_project.ipynb` выполняется `Restart & Run All`.
   - Структура соответствует описанной в разделе 8.1.
   - В начале ноутбука есть список участников и их вклад.
   - В каждом ключевом разделе есть текстовые выводы (ноутбук не является «голой тетрадкой с кодом»).

3. **ТЗ курса**
   - Покрыты этапы 0–4 (парсинг, предобработка, новые признаки, EDA, визуализации).
   - Есть минимум 2 новых признака (фактически их гораздо больше).
   - Есть разведочный анализ, корреляционная матрица и минимум 3 графика разных типов (фактически больше).
   - Оформление ноутбука и глубина анализа позволяют претендовать на доп. балл.

4. **Продукт Skillra**
   - Реализована «карта рынка»: зарплаты по городам/уровням/ролям, формат работы.
   - Реализован анализ навыков: частоты, премии, heatmap по грейдам.
   - Реализован анализ бенефитов и soft‑skills.
   - Есть 2–3 персоны с таблицами и графиками skill‑gap.
   - README объясняет, как этот проект ложится в MVP‑версию Career & Job Market Navigator.

При выполнении всех пунктов проект готов к демонстрации инвесторам, клиентам и академическому руководителю.
