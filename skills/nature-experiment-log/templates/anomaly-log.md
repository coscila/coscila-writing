# Anomaly log

Record all experimental anomalies for subsequent quality control and troubleshooting.

## Format

```yaml
---
date: YYYY-MM-DD
related_exp: EXP-ID
anomaly_type: equipment failure / operator error / unexpected result / safety incident
severity: low / medium / high
status: pending / resolved / recheck needed
---

## Description

[Objective description of the anomaly]

## Impact

[Assessment of its effect on experimental results]

## Response

[Measures already taken]

## Notes

[Recommended follow-up]
```

## Use

- Check for anomalies after every experiment.
- Append any anomaly to this file.
- Review unresolved anomalies regularly.
