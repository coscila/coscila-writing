# Test: unclear revision decision type

## Input

```text
Reviewer 1:
1. Please clarify the validation design.

Reviewer 2:
1. The Discussion should better explain the study limitations.

Prepare a point-by-point response and manuscript revision plan.
```

## Expected behavior

- Recognize that this is normal revision-response work but the editorial decision type is missing.
- Ask one concise question before drafting: whether this is `Major Revision` or `Minor Revision`.
- If the user writes Chinese, ask: `Is this a Major Revision or Minor Revision? If the decision letter does not specify, share it so I can help classify the decision.`
- Pause substantive response strategy and response-letter drafting until the user answers or supplies the decision letter.

## Forbidden behavior

- Do not infer Major Revision from the validation comment.
- Do not infer Minor Revision from the small number of visible comments.
- Do not produce a generic point-by-point response that treats both decision types as equivalent.
- Do not ask again if a subsequently supplied editor letter explicitly states the decision type.

## Pass/fail checklist

- [ ] The decision-type question is asked before substantive drafting.
- [ ] No revision type is guessed.
- [ ] No Major/Minor strategy is selected prematurely.
- [ ] The user is invited to provide the decision letter if its wording is unclear.
