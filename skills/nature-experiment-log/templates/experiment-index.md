# Experiment index

Dataview entry point that automatically lists experiment logs.

```dataview
TABLE date, salt_system, exp_type, material, anomaly
FROM "experiment-logs"
WHERE exp_id
SORT date DESC
```

## Use

1. Put this file in the vault's `experiment-logs/` directory.
2. Include YAML frontmatter in every log (`exp_id`, `date`, `salt_system`, `exp_type`, etc.).
3. Open it in Obsidian to view the interactive experiment list.

## Customize

Adjust query fields for your experimental systems. Common additions:

- Filter by system: `WHERE salt_system = "chloride salt"`.
- Filter by anomaly: `WHERE anomaly = true`.
- Filter by date: `WHERE date >= date(2026-01-01)`.
