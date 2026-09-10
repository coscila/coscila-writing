# Example experiment log: thermal stability

This complete thermal-stability log uses fictional data.

---

```yaml
---
exp_id: HY-T-260601-001
date: 2026-06-01
salt_system: mixed-salt system
salt_batch: HY-B1-B001
salt_composition: "*** (*** wt%)"
exp_type: thermal-stability
furnace: tube-furnace-1
crucible: AL-005
total_salt_mass_g: 40.0
temperature_profile: "RT→200°C(4h,dehydration)→500°C(8h)→700°C(2h)→furnace cooling"
atmosphere: "Ar (100 mL/min)"
condensate: "Collected 2.3 g of colorless liquid"
absorption_solution: "0.1M NaOH 50mL"
anomaly: false
anomaly_ref:
tags: [thermal-stability, tube furnace, Ar atmosphere]
---

# Experimental objective

Evaluate candidate B1's thermal stability under Ar and determine high-temperature mass loss and decomposition products.

# Procedure

1. Prepare 40.0 g of B1 salt in the glovebox and transfer to an alumina crucible
2. Dry in a tube furnace under Ar (100 mL/min) at 200°C for 4 h to remove adsorbed water
3. Heat to 500°C for 8 h, then 700°C for 2 h
4. Connect the outlet to a condenser and a NaOH absorption bottle
5. Sample and record each temperature stage; weigh after furnace cooling

# Observations

- No clear change during the 200°C stage
- Approximately 2.3 g of colorless liquid condensed at 500°C, possibly crystal water or low-boiling components
- At 700°C the salt changed from white to pale yellow without clear decomposition
- Condensate pH approximately 6 (weakly acidic)

# Results

- Total mass loss: 11.5% of initial mass
- Most mass loss occurred at 200–500°C (dehydration); loss at 500–700°C was only 1.2%
- ICP-OES of residual salt showed no clear change in component proportions
- Thermal stability passed the stated assessment

# Anomalies

None.

# Next steps

- Compare thermal stability of candidates B2 and B3
- Extend the 700°C hold to 24 h to assess long-term stability
- Quantify residual water by Karl Fischer titration

---

# Original material

`raw/experiments/2026.06.01_B1thermal-stability_HY-T-260601-001/`
