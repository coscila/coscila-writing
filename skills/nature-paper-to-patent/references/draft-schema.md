# Structured Draft Schema

## Contents

- [Purpose](#purpose)
- [Rules](#rules)


## Purpose

Populate a UTF-8 JSON file with this structure before rendering a DOCX. Empty optional arrays are allowed. Preserve `[TO CONFIRM: ...]` markers where facts remain unresolved.

```json
{
  "schema_version": "2.0",
  "title": "A method, apparatus and medium for …",
  "metadata": {
    "source": "paper.pdf",
    "target": "Chinese invention patent",
    "draft_status": "For inventor and patent-professional review"
  },
  "source_analysis": {
    "contains_core_formulas": true,
    "formula_count_in_source": 18,
    "contains_methodology_figures": true
  },
  "source_map": [
    {
      "id": "P001",
      "type": "paper-text",
      "locator": "page 3, section 2.2, paragraph 1",
      "summary": "Discloses the core feature-extraction process",
      "confidence": "high"
    },
    {
      "id": "E001",
      "type": "equation",
      "locator": "page 4, equation (1)",
      "summary": "Class-prototype calculation",
      "confidence": "high"
    }
  ],
  "terminology_ledger": [
    {
      "concept": "class prototype",
      "canonical_zh": "类别原型",
      "source_terms": ["class prototype", "prototype"],
      "forbidden_aliases": ["class center"]
    }
  ],
  "formula_inventory": [
    {
      "source_id": "E001",
      "source_number": "(1)",
      "technical_role": "Compute class prototypes from support-set features",
      "disposition": "specification-equation-1"
    }
  ],
  "figure_inventory": [
    {
      "source_id": "F001",
      "source_number": "Fig. 2",
      "type": "methodology",
      "disposition": "redraw-as-figure-2"
    }
  ],
  "abstract_figure_number": 1,
  "assumptions": [
    "The target jurisdiction is China"
  ],
  "invention_concept": {
    "technical_problem": "……",
    "technical_means": "……",
    "technical_effect": "……"
  },
  "evidence_ledger": [
    {
      "id": "F1",
      "feature": "……",
      "source_ids": ["P001", "E001"],
      "source_location": "page 3, section 2.2",
      "technical_role": "……",
      "effect": "……",
      "support_status": "explicit"
    }
  ],
  "claims": [
    {
      "number": 1,
      "text": "A method for …, characterized by comprising: …"
    },
    {
      "number": 2,
      "text": "The method according to claim 1, characterized in that …"
    }
  ],
  "claim_feature_map": [
    {
      "claim_number": 1,
      "feature": "Compute class prototypes from support-set features",
      "evidence_ids": ["F1"],
      "specification_locations": ["Detailed embodiments, embodiment 1"]
    }
  ],
  "figures": [
    {
      "number": 1,
      "title": "Method flowchart",
      "type": "flowchart",
      "orientation": "vertical",
      "claim_number": 1,
      "complete_claim_flow": true,
      "source_ids": ["P001"],
      "nodes": [
        {
          "id": "S1",
          "label": "S1: Obtain and preprocess data to be examined",
          "claim_step": "S1"
        },
        {
          "id": "S2",
          "label": "S2: Extract multiscale features",
          "claim_step": "S2"
        }
      ],
      "edges": [
        {
          "from": "S1",
          "to": "S2",
          "label": ""
        }
      ]
    },
    {
      "number": 2,
      "title": "Core method architecture diagram",
      "type": "methodology",
      "orientation": "horizontal",
      "source_ids": ["F001", "P001"],
      "nodes": [
        {
          "id": "input",
          "label": "Input features"
        },
        {
          "id": "module",
          "label": "Core processing module"
        },
        {
          "id": "output",
          "label": "Output features"
        }
      ],
      "edges": [
        {
          "from": "input",
          "to": "module",
          "label": ""
        },
        {
          "from": "module",
          "to": "output",
          "label": ""
        }
      ]
    }
  ],
  "specification": {
    "technical_field": [
      "The invention relates to …"
    ],
    "background": [
      "……"
    ],
    "invention_content": {
      "problem": [
        "……"
      ],
      "solution": [
        "……"
      ],
      "beneficial_effects": [
        "……"
      ]
    },
    "figure_descriptions": [
      "Figure 1 shows the invention method flowchart."
    ],
    "equations": [
      {
        "number": 1,
        "source_location": "paper page 4, equation (1)",
        "source_ids": ["E001"],
        "expression": "O_u = (1/|S_u|) Σ_(x_i,y_i∈S_u) h_γ(x_i)",
        "latex": "O_u = \\frac{1}{|S_u|}\\sum_{(x_i,y_i)\\in S_u} h_\\gamma(x_i)",
        "symbols": [
          {"symbol": "O_u", "meaning": "class prototype for class u"},
          {"symbol": "S_u", "meaning": "support set for class u"},
          {"symbol": "h_\\gamma", "meaning": "supervised feature extractor"}
        ],
        "technical_role": "Average the supervised features of samples in the same class to obtain a class prototype",
        "description": "Here O_u denotes the prototype of class u, S_u its support set, and h_γ the supervised feature extractor. The formula obtains the class prototype by averaging supervised features from samples of that class."
      }
    ],
    "embodiments": [
      {
        "heading": "Embodiment 1",
        "paragraphs": [
          "……"
        ]
      }
    ]
  },
  "abstract": "The invention relates to …",
  "audit": {
    "support_findings": [
      "……"
    ],
    "consistency_findings": [
      "……"
    ]
  },
  "quality_assessment": {
    "status": "review-draft",
    "scores": {
      "evidence_support": {"score": 4, "evidence": "Every claim feature maps to the evidence ledger."},
      "claim_architecture": {"score": 4, "evidence": "The independent claim forms a complete technical chain with dependent fallback claims."},
      "terminology_consistency": {"score": 4, "evidence": "Claims, specification and drawings use consistent terminology."},
      "enablement_detail": {"score": 3, "evidence": "The main data flows, formulas and implementation steps are explained."},
      "technical_effect_reasoning": {"score": 3, "evidence": "The principal effects are linked to the corresponding technical means."},
      "formula_coverage": {"score": 4, "evidence": "All core formulas are included and their symbols defined."},
      "figure_alignment": {"score": 4, "evidence": "The main flowchart matches the steps in claim 1."}
    }
  },
  "inventor_questions": [
    "[TO CONFIRM: ……]"
  ]
}
```

## Rules

- Use integer claim numbers in ascending order.
- Use stable source IDs: `P` for paper text, `E` for equations, `F` for
  source figures, and `C` for code or supplementary evidence.
- Give every `explicit` or `inherent` evidence-ledger item one or more
  `source_ids`.
- Add at least one `claim_feature_map` entry for every formal claim. Map each
  material limitation to evidence-ledger IDs, not merely to a general page.
- Store claim text without repeating the number at its beginning.
- Use arrays for paragraphs to preserve paragraph boundaries.
- Use only `explicit`, `inherent`, `needs-confirmation`, or `unsupported` as evidence status.
- Exclude unsupported features from formal claims.
- Keep internal audit material in the appendix, not in the formal application sections.
- Number figures consecutively from 1.
- Set `abstract_figure_number` to the main figure used as the abstract figure.
- Reuse that exact figure in the specification; do not create a conflicting duplicate.
- The abstract figure should normally be an overall method or system flow that represents the principal independent claim.
- Use `flowchart` as the figure type and `vertical` or `horizontal` as the orientation.
- Use `methodology` for an intermediate architecture, module, feature-flow, or loss-relationship figure.
- A methodology figure does not require `claim_number`, `claim_step`, or `complete_claim_flow`.
- Prefer a paper figure when suitable; otherwise redraw it as a concise black-and-white patent figure.
- Give every node a unique ASCII identifier.
- Keep `claim_step` equal to the corresponding identifier in the method claim, such as `S1`.
- Set `claim_number` to the method claim represented by the figure.
- Set `complete_claim_flow` to `true` for an overall flowchart that must cover every numbered step in that claim.
- Reference every figure in `specification.figure_descriptions`.
- Use concise node labels; put implementation detail in the specification.
- If the paper contains formulas that define core technical operations, populate `specification.equations`.
- Set `source_analysis.contains_core_formulas` after reviewing the paper.
- Number equations consecutively from 1.
- Add a valid `latex` field to every equation; the renderer converts it to editable Office Math.
- Add `source_ids`, structured `symbols`, and `technical_role` to every
  equation.
- Treat `expression` as a readable audit copy, not as the DOCX rendering source.
- Record the paper page and original formula number in `source_location`.
- Define every symbol in `description` and state the technical operation performed by the formula.
- Include formulas in the standalone specification DOCX; do not place them only in an internal appendix.
- Record a disposition for every core source formula and methodology figure.
- Populate `quality_assessment.scores` with a 1-5 score and evidence sentence
  for each dimension required by `static/core/output-contract.md`.

Translation note: `canonical_zh` intentionally retains the original Chinese term for “class prototype”; this schema field is the canonical Chinese terminology value used when preparing a Chinese application. Other sample prose is translated for English readers.
