# Example experiment log: electrochemical testing

This complete electrochemical-characterization log uses fictional data.

---

```yaml
---
exp_id: OX-E-260615-001
date: 2026-06-15
salt_system: oxide system
salt_batch: OX-A1-B001
salt_composition: "*** (*** wt%)"
exp_type: electrochemistry
test_method: CV
working_electrode: Pt wire
counter_electrode: Pt mesh
reference_electrode: "Ag/Ag+ quasi-reference"
temperature: 500
atmosphere: Ar
potential_window_V: "-1.5 ~ +1.0"
scan_rate_mV_s: 50
evaluation_target: "Measure the electrochemical window and impurity redox peaks"
anomaly: false
anomaly_ref:
tags: [electrochemistry, CV, window-test]
---

# Experimental objective

Measure the electrochemical window of candidate A1 at 500°C to assess suitability for subsequent corrosion experiments and detect impurity redox peaks.

# Procedure

1. Prepare 30 g of A1 salt in the glovebox and transfer to an alumina crucible
2. Dry in a muffle furnace at 300°C for 2 h to remove adsorbed water
3. Transfer to the electrochemical test station and heat to 500°C under Ar
4. Three-electrode system: Pt-wire working electrode, Pt-mesh counter electrode, Ag/Ag+ quasi-reference
5. CV scan: -1.5 V to +1.0 V at 50 mV/s
6. Record three cycles and use the third as steady-state data

# Observations

- The molten salt was transparent with no clear suspended material
- Small CV peaks appeared at -0.8 V and +0.6 V, tentatively attributed to impurities
- No visible electrode-surface corrosion

# Results

- Electrochemical window approximately 2.5 V (-1.5 to +1.0 V), suitable for subsequent corrosion experiments
- Further EIS is needed to establish system stability
- Identify impurity peaks using standard addition

# Anomalies

None.

# Next steps

- Long-duration EIS stability test (100 h)
- Assign impurity peaks to species by standard addition
- Compare window widths with candidates A2 and A3

---

# Original material

Original images and audio records are archived at:
`raw/experiments/2026.06.15_A1electrochemical-window-test_OX-E-260615-001/`

- `images/IMG_6151.jpg` — Three-electrode test-station layout
- `images/IMG_6152.jpg` — CV trace screenshot
