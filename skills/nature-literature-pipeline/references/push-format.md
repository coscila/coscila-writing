# Feishu Push Format

> Daily literature digest template delivered to the dedicated Feishu group.
> The `{placeholder}` values are filled by the fine-reading stage.

## Template

```markdown
📅 {YYYY-MM-DD} Literature daily digest | Research Field Daily

━━━━━━━━━━━━━━━━━━━━

🏅 #{N} | {Title}
{Journal/Source}, {Year} | {Authors} et al. | {Institution} | ⭐ {score}/10 | Classification: {A-E tier}
DOI: {doi if available} | arXiv: {arxiv_id if available}

💡 Takeaway：{one-line takeaway — why this paper matters or why it is only deferred}

🔬 Methods：{experiment/simulation, salt system, temperature, alloy/coating, characterization/electrochemical techniques}

📊 Key results：{specific data or conclusions, with units and test conditions; no vague summaries}

🧭 Assessment：{value to the research mainline, limitations, whether worth full-text reading}

📎 {best available link: DOI / arXiv / PDF / repository}

━━━━━━━━━━━━━━━━━━━━

🏅 #{N+1} | ...
```

Daily pushes should NOT include a fixed "Connection to the vault" field or forced wiki links; that's low-information. Vault/wiki connections belong in archival notes and later manual wiki integration. If a paper clearly hits a tracked author/network, mention it naturally in the commentary.

## Field Guidelines

| Field | Principle |
|-------|-----------|
| 💡 Takeaway | Let readers decide within 15 seconds whether to open the paper; state its core contribution concretely |
| 🔬 Methods | Experiment or simulation? Which salt system, characterization (CV/EIS/SEM/XRD/TEM), and alloy? |
| 📊 Key results | Require specific data or explicit conclusions; avoid vague claims such as important findings or new perspectives |
| 🧭 Assessment | Explain practical value to the research topic, limitations and whether full reading is worthwhile; do not force a vault connection |
| ⭐ Score | Screening score (0–10) indicates priority; internal six-dimension scoring remains 0–100 with per-dimension bounds |

## Example

All papers, identifiers, dates, and numerical results in this example are synthetic.

```markdown
📅 YYYY-MM-DD Literature daily digest | Research Field Daily

━━━━━━━━━━━━━━━━━━━━

🏅 #1 | Electrochemical monitoring of impurity X in compound A-B-C system via advanced voltammetry
Electrochimica Acta, 2026 | Zhang, Li, Wang et al. | CAS Institute | ⭐ 9.2/10 | Classification: A_核心主线
DOI: <DOI> | arXiv: <ARXIV_ID>

💡 Takeaway：First application of method X to system Y for impurity quantification, detection limit improved ~5× over prior art。

🔬 Methods：500°C MgCl₂-KCl-NaCl; Pt working electrode, Ag/AgCl reference; Ar with varied H₂O partial pressures; SWV quantifies MgOHCl with titration cross-checking.

📊 Key results：
  · SWV detection limit: 8 ppm O（vs. prior art CV method ~39 ppm）
  · Peak current is linear with MgOHCl concentration: R²=0.997 over 0–200 ppm
  · Peak-position drift <5 mV during a 200 h stability test

🧭 Assessment：Tier A candidate. SWV improves impurity-monitoring sensitivity over CV, supporting a monitoring-control-validation cycle; full-text checking is needed for reference-electrode stability and calibration.

📎 https://example.org/paper

━━━━━━━━━━━━━━━━━━━━

🏅 #2 | ...
```

## Delivery

```python
send_message(
    target="feishu:<chat_id>",
    message="<formatted_digest>"
)
```

Use `send_message(action='list')` to discover the chat_id if unknown. The target must be a group the Hermes bot has been added to as a member (Feishu group settings → bots → add).
