# CODEx_DIFF_PLAN.md — дифф‑план до целевого состояния

Репозиторий: `skillra_hse_pda`  
Версия плана: 2025‑12‑10

Цель: начиная с текущей кодовой базы, довести проект до целевого состояния, описанного в `CODEx_PLAN.md`, без ломки существующей архитектуры.

---

## 0. Стартовые предпосылки

- Есть работающие модули `cleaning.py`, `features.py`, `eda.py`, `viz.py`, `personas.py`, `io.py`, `config.py`.
- Есть `notebooks/01_hse_project.ipynb`, который уже закрывает базовые этапы ТЗ.
- Есть `scripts/validate_pipeline.py`.
- Нет:
  - полноценного `scripts/run_pipeline.py`,
  - модуля `market.py`,
  - тестов в `tests/`,
  - расширенного EDA по доменам/английскому/образованию/работодателям,
  - high‑level API `analyze_persona`.

---

## 1. EDA по доменам (domain_*)

**Цель:** использовать признаки `domain_*` для отраслевого анализа.

### 1.1. `src/skillra_pda/eda.py`

Добавить функции:

1. `extract_primary_domain(df: pd.DataFrame, domain_prefix: str = "domain_") -> pd.Series`  
   - Определяет основной домен вакансии:
     - если ни один `domain_*` не True → `"unknown"`;
     - если несколько True → можно взять первый по алфавиту или в фиксированном списке приоритетов.
   - Возвращает pd.Series с названием домена.

2. `describe_salary_by_domain(df: pd.DataFrame, salary_col: str = "salary_mid_rub_capped") -> pd.DataFrame`  
   - Использует `extract_primary_domain`.
   - Возвращает таблицу с колонками:
     - `domain`
     - `vacancy_count`
     - `share`
     - `salary_q25`
     - `salary_median`
     - `salary_q75`.

### 1.2. `src/skillra_pda/viz.py`

Добавить функцию:

- `salary_by_domain_plot(df: pd.DataFrame, top_n: int = 10, savepath: Optional[Path] = None) -> Path`  
  - Использует `eda.describe_salary_by_domain`.
  - Берёт top_n доменов по `vacancy_count`.
  - Строит barplot медианной зарплаты по доменам.
  - Сохраняет в `reports/figures/fig_salary_by_domain.png` по умолчанию.

### 1.3. `notebooks/01_hse_project.ipynb`

Добавить раздел EDA:

- «Рынок по доменам (отраслям)»:
  - вывод таблицы `describe_salary_by_domain`,
  - вызов `salary_by_domain_plot`,
  - 3–5 bullet‑выводов (где выше зарплаты, где больше вакансий, насколько домены отличаются).

---

## 2. EDA по английскому и образованию

**Цель:** показать влияние требований к языку и образованию.

### 2.1. `src/skillra_pda/eda.py`

Добавить:

1. `english_requirement_stats(df: pd.DataFrame) -> pd.DataFrame`  
   - На основе доступных колонок (например, `lang_english_required`, уровни английского) формирует категории уровня (например, `"no_english"`, `"A2"`, `"B1"`, `"B2"`, `"C1_plus"`).
   - Возвращает таблицу:
     - `english_level`
     - `vacancy_count`
     - `share`
     - `salary_median`.

2. `education_requirement_stats(df: pd.DataFrame) -> pd.DataFrame`  
   - Использует признаки `edu_*` (если есть).
   - Формирует категории типа:
     - `"no_degree_required"`, `"any_degree"`, `"technical_only"`, `"master_phd"` (подогнать под реальные данные).
   - Возвращает:
     - `education_level`
     - `vacancy_count`
     - `share`
     - `salary_median`.

### 2.2. `src/skillra_pda/viz.py`

Добавить:

1. `salary_by_english_level_plot(df: pd.DataFrame, savepath: Optional[Path] = None) -> Path`  
   - Использует `english_requirement_stats`.
   - Barplot median salary по `english_level`.
   - Сохраняет `fig_salary_by_english_level.png`.

2. `salary_by_education_level_plot(df: pd.DataFrame, savepath: Optional[Path] = None) -> Path`  
   - Использует `education_requirement_stats`.
   - Barplot median salary по `education_level`.
   - Сохраняет `fig_salary_by_education_level.png`.

### 2.3. `notebooks/01_hse_project.ipynb`

Добавить раздел EDA:

- «Английский и образование»:
  - вывод таблиц `english_requirement_stats` и `education_requirement_stats`,
  - вставка соответствующих графиков,
  - текстовые выводы:  
    - доля вакансий с английским B2+,  
    - примерная премия за английский,  
    - доля вакансий, где не нужен диплом / нужен технарь,  
    - есть/нет премия за высшее/техобразование.

---

## 3. EDA по работодателям, бенефитам и soft‑skills

**Цель:** использовать идеи из `notebooks/Group_project_draft.ipynb`.

### 3.1. `src/skillra_pda/eda.py`

Добавить:

1. `top_employers(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame`  
   - Группировка по колонке работодателя (например, `employer_name` или аналогичной).
   - Возвращает:
     - `employer`
     - `vacancy_count`
     - `salary_median`.

2. `benefits_by_employer(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame`  
   - Выбирает top_n работодателей.
   - Для каждого `benefit_*` считает долю вакансий с этим флагом.
   - Возвращает pivot employer × benefit.

3. `soft_skills_by_employer(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame`  
   - Аналогично, но для `soft_*`.

### 3.2. `src/skillra_pda/viz.py`

Добавить:

1. `benefits_employer_heatmap(df: pd.DataFrame, top_n: int = 10, savepath: Optional[Path] = None) -> Path`.
2. `soft_skills_employer_heatmap(df: pd.DataFrame, top_n: int = 10, savepath: Optional[Path] = None) -> Path`.

Обе функции:

- используют соответствующие EDA‑функции,
- рисуют heatmap employer × feature,
- сохраняют картинки в `reports/figures/` (имена типа `fig_benefits_by_employer_heatmap.png`, `fig_soft_skills_by_employer_heatmap.png`).

### 3.3. `notebooks/01_hse_project.ipynb`

Добавить раздел:

- «Топ работодатели, бенефиты и soft‑skills»:
  - таблица `top_employers`,
  - 2 heatmap (бенефиты и soft),
  - выводы (кто щедр на бенефиты, кто требует soft‑skills, видно ли связь с зарплатами).

---

## 4. Прокачка personas и product‑API

**Цель:** использовать персоны как стабильный API для продукта Skillra.

### 4.1. `src/skillra_pda/personas.py`

1. Расширить dataclass `Persona`:

   ```python
   @dataclass
   class Persona:
       name: str
       current_skills: List[str]
       target_role: str
       target_grade: str | None = None
       target_city_tier: str | None = None
       target_work_mode: str | None = None
       constraints: Dict[str, object] = field(default_factory=dict)
    ```

   * Обновить существующие примеры персон под эту схему (если они есть).

2. Убедиться, что есть функция `build_skill_demand_profile(df, persona, ...)`:

   * фильтрует вакансии под целевой сегмент персоны,
   * считает долю вакансий с каждым skill (по префиксам `has_`, `skill_`, опционально `soft_`).

3. Переписать/уточнить `skill_gap_for_persona(df, persona, top_k)`:

   * использовать `build_skill_demand_profile`,
   * возвращать DataFrame с колонками:

     * `skill`, `market_share`, `persona_has`, `gap`.

4. Добавить high‑level функцию:

   ```python
   def analyze_persona(df: pd.DataFrame, persona: Persona, top_k: int = 10) -> dict:
       """
       Возвращает:
         - market_summary: dict (count вакансий, median/q25/q75 зарплат, remote_share, junior_friendly_share и т.п.)
         - skill_gap: pd.DataFrame (как в skill_gap_for_persona)
         - recommended_skills: list[str] (список навыков с gap, отсортированных по market_share)
       """
   ```

### 4.2. `notebooks/01_hse_project.ipynb`

* В разделе про персоны заменить ручную работу с gap на использование `analyze_persona`:

  * для каждой персоны выводить:

    * краткое описание,
    * market_summary,
    * таблицу skill_gap,
    * текст с рекомендациями (3–5 навыков для прокачки).

---

## 5. Market view витрина

**Цель:** агрегированный датасет для UI/агента Skillra.

### 5.1. Новый модуль `src/skillra_pda/market.py`

Создать модуль с функцией:

```python
def build_market_view(df_features: pd.DataFrame) -> pd.DataFrame:
    """
    Группирует вакансии по (primary_role, grade, city_tier[, домен]) и считает агрегаты:
      - vacancy_count
      - salary_q25, salary_median, salary_q75 (по salary_mid_rub_capped)
      - junior_friendly_share
      - remote_share
      - median_tech_stack_size (или аналогичный показатель)
      - top_skills (строка с топ-3–5 навыками сегмента)
    """
```

### 5.2. `scripts/run_pipeline.py`

Создать скрипт, который:

1. Загружает сырой CSV из `config.RAW_DATA_FILE` (через `io` или напрямую).
2. Прогоняет через пайплайн cleaning:

   * парсинг дат (если есть),
   * нормализация булевых,
   * обработка пропусков,
   * подготовка зарплат,
   * `deduplicate`.
3. Сохраняет чистый датасет в `config.CLEAN_DATA_FILE`.
4. Прогоняет через `features.assemble_features` (или аналогичный high‑level helper).
5. Сохраняет фичи в `config.FEATURE_DATA_FILE`.
6. Вызывает `market.build_market_view(df_features)` и сохраняет результат как `data/processed/market_view.parquet`.

---

## 6. Тесты и validate_pipeline

### 6.1. Добавить `tests/`

Создать каталог `tests/` и минимальный набор:

1. `tests/test_cleaning.py`:

   * тест, что `ensure_salary_gross_boolean` корректно чистит `"unknown"` и приводит к nullable boolean;
   * тест, что функция обработки пропусков дропает почти пустые колонки (если такая есть).

2. `tests/test_features.py`:

   * тест, что `add_city_tier` правильно классифицирует Москву/СПб/миллионники;
   * тест, что `add_primary_role` выбирает роль в нужном приоритете.

3. `tests/test_personas.py`:

   * тест для `build_skill_demand_profile` + `skill_gap_for_persona` на маленьком искусственном DataFrame.

### 6.2. Улучшить `scripts/validate_pipeline.py`

* После выполнения пайплайна (как минимум загрузки и сохранения) выводить:

  * `dtype` и долю `"unknown"` для `salary_gross` до/после,
  * `df.attrs["deduplicated_rows"]`, `df.attrs["dropped_columns"]` (если атрибуты есть).
* Сделать сообщения читаемыми в консоли.

---

## 7. Документация

### 7.1. `docs/02_feature_dictionary_hh.md`

* Обновить/добавить описания для:

  * `city_tier`
  * `work_mode`
  * `salary_mid_rub_capped`
  * `salary_bucket`
  * `salary_known`
  * `tech_stack_size` / агрегаты по навыкам
  * `benefits_count`, `soft_skills_count`, `role_count`
  * `primary_role`
  * `is_junior_friendly`, `battle_experience`
  * всех новых фичей, добавленных по ходу задач.

### 7.2. README и/или docs

* В `README.md`:

  * кратко описать:

    * как запускать пайплайн (`python scripts/run_pipeline.py`),
    * какие файлы появляются в `data/processed/`,
    * как использовать `market_view` и `analyze_persona`.
* При необходимости обновить `docs/01_product_context_skillra.md` (как Python‑часть ложится в MVP Skillra).

---

## 8. Финальный проход

После выполнения всех задач:

1. Убедиться, что:

   * `python scripts/validate_pipeline.py` проходит без ошибок;
   * `python scripts/run_pipeline.py` отрабатывает и создаёт все нужные файлы;
   * `pytest` (если установлен) проходит на добавленных тестах;
   * `notebooks/01_hse_project.ipynb` выполняется **Run All**.

2. Проверить, что все новые функции имеют docstring’и, а новые признаки описаны в `docs/02_feature_dictionary_hh.md`.

3. В конце ноутбука обновить раздел с итоговыми выводами, учитывая новые EDA (домены, английский, образование, работодатели).