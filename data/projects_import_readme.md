# CSV Project Importer

Use this command to bulk create or update `Project` rows.

## Command

```powershell
c:/Users/USER/PycharmProjects/PythonProject1/.venv/Scripts/python.exe manage.py import_projects_csv <csv_path>
```

## Recommended workflow

1. Dry run first:

```powershell
c:/Users/USER/PycharmProjects/PythonProject1/.venv/Scripts/python.exe manage.py import_projects_csv data/projects_import_template.csv --dry-run
```

2. Real import (create only):

```powershell
c:/Users/USER/PycharmProjects/PythonProject1/.venv/Scripts/python.exe manage.py import_projects_csv data/projects_import_template.csv
```

3. Real import with updates for existing records:

```powershell
c:/Users/USER/PycharmProjects/PythonProject1/.venv/Scripts/python.exe manage.py import_projects_csv data/projects_import_template.csv --update-existing
```

## How existing projects are matched

A row is treated as existing if `title + field + target_role` matches an existing `Project`.

- Without `--update-existing`: existing rows are skipped.
- With `--update-existing`: existing rows are updated.

## Required CSV columns

- `title`
- `description`
- `field`
- `target_role`
- `skill_level` (`beginner`, `intermediate`, `advanced`)
- `required_plan` (`explorer`, `pro_monthly`, `pro_yearly`)
- `tech_preference`
- `learning_goal`
- `interest_tags`

## Optional CSV columns

- `learning_objectives`
- `resources`
- `task_checklist`
- `detailed_roadmap`
- `github_starter_template` (legacy column, currently ignored)
- `premium_hints`

## Notes

- The importer accepts common aliases for plans (`free`, `monthly`, `yearly`, etc.).
- For multiline fields in CSV (like checklists), use quoted values with line breaks.
- Template file is available at `data/projects_import_template.csv`.
