# Example experiment log

This complete material-corrosion immersion log uses fictional data solely to demonstrate the format and recording conventions.

---

```yaml
---
exp_id: CL-M-260529-001
date: 2026-05-29
salt_system: chloride salt
salt_batch: CL-Q1-B001
salt_composition: "Q1 (*** mol%)"
exp_type: corrosion-test
furnace: muffle-furnace-1
crucible: AL-001
total_salt_mass_g: 50.0
temperature_profile: "RT→300°C(2h,drying)→500°C(300h)→furnace cooling"
atmosphere: Ar
material: 316L
material_category: austenitic stainless steel
sample_id: 316L-2026-001
sample_dimensions_mm: "20×10×2"
sample_surface: "SiC 1200 grit"
pre_mass_g: 3.4521
post_mass_g: 3.4489
mass_loss_g: 0.0032
corrosion_rate_um_year: ***
anomaly: false
anomaly_ref:
tags: [chloride salt, corrosion-test, 316L, Q1]
---

# Experimental objective

Evaluate corrosion of 316L austenitic stainless steel in candidate formulation Q1 at 500°C as a baseline for screening a quaternary chloride-salt system.

# Procedure

1. Prepare 50.0 g of Q1 salt and mix thoroughly in the glovebox
2. Polish the 316L sample with 1200-grit SiC, ultrasonically clean with acetone, dry, and weigh
3. Dry in a muffle furnace under Ar at 300°C for 2 h to remove adsorbed water
4. Heat to 500°C and hold for 300 h
5. Allow the furnace to cool to room temperature and remove the sample
6. Ultrasonically clean with deionized water, dry, and weigh
7. Calculate mass loss and corrosion rate

# Observations

- The cooled salt formed a transparent pale-yellow glass with no clear stratification
- The sample lost its metallic luster and became uniformly dark gray
- No visible corrosion on the crucible's inner wall
- No abnormal gas release or splashing observed

# Results

- Sample mass loss: 0.0032 g (0.09%)
- No clear localized corrosion or pitting
- Corrosion-product composition awaits XRD and SEM-EDS confirmation

# Anomalies

None.

# Next steps

- Use cross-sectional SEM-EDS to examine corrosion-layer structure and Cr depletion
- Identify corrosion-product phases by XRD
- Compare parallel experiments with candidate formulations Q2 and Q3

---

# Original material

Original images and audio records are archived at:
`raw/experiments/2026.05.29_Q1corrosion-test_316L_CL-M-260529-001/`

- `images/IMG_5291.jpg` — Sample surface before corrosion
- `images/IMG_5292.jpg` — Sample surface after corrosion
- `images/IMG_5293.jpg` — Crucible interior after salt cooling
