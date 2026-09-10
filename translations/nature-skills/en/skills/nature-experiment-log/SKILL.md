---
name: nature-experiment-log
description: "Standardize experiment logs from uploaded or local images, voice recordings and text; produce Markdown with YAML frontmatter, with optional Feishu CLI and Obsidian integration."
license: MIT
metadata:
  author: Jiahao8595
  hermes:
    tags: [research, experiment, logging, feishu, obsidian, automation]
    related_skills: [nature-literature-pipeline, feishu-cli-integration, obsidian]
---

# experiment-log — Standardized experiment logging

## Input

Load when the user supplies original experimental material through:

- **Direct upload:** images, audio, transcripts or text in the current conversation.
- **Local material:** file or folder paths to read and organize.
- **Feishu group:** messages and attachments through optional `feishu-cli-integration`.

## Output

- **Local Markdown:** save logs and original attachments in the user's selected ordinary local
  folder. If none is specified, first return saveable Markdown rather than choosing a path.
- **Obsidian vault:** optionally use the `obsidian` skill and supplied index, anomaly and equipment templates.

The core flow requires neither Feishu nor Obsidian. Feishu input requires the bot to belong
to the target group and have `im:message`, `im:message.group_msg`, and `im:resource` permissions.

## Procedure

1. Receive uploads, read local files, or retrieve material from a configured Feishu group.
2. Extract structured information using vision_analyze and text parsing.
3. Clarify missing or ambiguous fields; never guess experimental conditions or results.
4. Confirm the output route and destination; generate experiment and sample-batch IDs.
5. Write `{OUTPUT_ROOT}/experiment-logs/{system}/{type}/{exp_id}.md`.
6. Archive original attachments at `{OUTPUT_ROOT}/raw/experiments/YYYY.MM.DD_description_EXPID/` and link them in the log.
7. Update the experiment index if enabled; append an anomaly record when needed.
8. Report exact generated-file and original-material locations.

Ask about uncertain temperatures or sample identifiers rather than guessing.

## Directory layout

```text
/vault/
├── raw/experiments/                       ← original archive
│   └── YYYY.MM.DD_description_EXPID/
│       ├── notes.md
│       ├── images/
│       └── audio/
│
wiki/experiment-logs/                      ← standardized outputs
├── experiment-index.md
├── anomaly-log.md
├── {system-A}/
│   ├── experiment-type-1/
│   ├── experiment-type-2/
│   └── ...
├── {system-B}/
│   └── ...
└── shared/
    └── equipment-tracking.md
```

## Experiment IDs

```text
{system-code}-{equipment-code}-YYMMDD-{sequence}
```

Sequence starts at 001 each day. Equipment codes: M=muffle furnace, T=tube furnace,
E=electrochemistry, G=glovebox, F=controlled-atmosphere furnace, B=general purpose.
Choose system codes for the laboratory, e.g. CL, NO, OX or HY.

## Sample-batch IDs

```text
{system-code}-{candidate-number}-B{sequence}
```

Use the candidate formulation number and salt-preparation batch sequence. Keep `sample_batch`
unchanged across experiments using the same batch so Dataview can track it.

## Equipment codes

| Code | Equipment | Use |
|---|---|---|
| M | Muffle furnace | Heat treatment, immersion corrosion |
| T | Tube furnace | Atmosphere control, dehydration, thermal stability |
| E | Electrochemical workstation | CV/SWV/EIS |
| G | Glovebox | Salt preparation, weighing, sampling |
| F | Controlled-atmosphere furnace | Precise atmosphere control |
| B | General purpose | Drying, cleaning, sample preparation |

Extend the codes for the equipment actually available.

## Optional Obsidian integration

Write Markdown to an ordinary local folder or an [Obsidian](https://obsidian.md) vault.
Obsidian stores local Markdown notes; [Dataview](https://github.com/blacksmithgu/obsidian-dataview)
can query experiment data and build dashboards.

Benefits:

- Plain-text logs support version control and full-text search.
- YAML frontmatter enables experiment lists, anomaly summaries and equipment-use records.
- Local storage avoids a cloud dependency.

Create these files in the vault after installing the skill:

| File | Template | Purpose |
|---|---|---|
| `experiment-logs/experiment-index.md` | `templates/experiment-index.md` | Dataview dashboard |
| `experiment-logs/anomaly-log.md` | `templates/anomaly-log.md` | Anomaly records |
| `experiment-logs/shared/equipment-tracking.md` | `templates/equipment-tracking.md` | Equipment and reagent tracking |

Copy templates to the corresponding vault paths.

## Examples

`references/` contains complete examples with YAML frontmatter and Markdown bodies:

| File | Experiment |
|---|---|
| `references/example-log.md` | Material corrosion immersion |
| `references/example-electrochemical.md` | Electrochemical characterization/CV window testing |
| `references/example-thermal-stability.md` | Thermal stability |

Adapt these examples as templates.

## Optional Feishu CLI integration

Use `feishu-cli-integration` when retrieving group material:

- List messages: `lark-cli im +chat-messages-list --chat-id oc_*** --page-size 30 --sort asc`
- Download images: `lark-cli im +messages-resources-download --message-id *** --file-key *** --type image --output <relative-path>`
- `--output` accepts only relative paths; first change directory to the `raw/experiments/` archive.

Obtain group IDs and bot permissions through the integration skill's configuration.

## Customization

- Define system codes such as CL/NO/OR/PO.
- Create experiment-type folders below `wiki/experiment-logs/{system}/`.
- Add/remove YAML fields; templates suggest a structure rather than fixing it.
- Extend equipment codes for the laboratory.
- Choose an ordinary local directory or a vault as the output root.

## Related files

| File | Purpose |
|---|---|
| `references/example-log.md` | Complete experiment log |
| `wiki/experiment-logs/experiment-index.md` | Dataview dashboard |
| `wiki/experiment-logs/anomaly-log.md` | Anomaly format |
| `wiki/experiment-logs/shared/equipment-tracking.md` | Equipment/reagent tracking |
