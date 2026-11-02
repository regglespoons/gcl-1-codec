# DTE Energy (DTE Electric) — Grid, Cost & Delivery Data Pack

Compiled Nov 1-2 2026 for the site interval analysis tool. Every figure carries
its source and date. Utility data ages: re-verify rates and plant status before
quoting anything to a client.

## 1. Territory and scale
- DTE Electric serves roughly 2.3 million customers in southeast Michigan
  (Detroit, Wayne/Oakland/Macomb/Washtenaw/St. Clair, plus Ann Arbor, Royal Oak,
  Birmingham). Gas side is separate; this pack is electric only.
- MISO is the balancing authority; DTE is a transmission-owning load-serving
  entity inside it. Local transmission is largely operated by ITC Holdings
  (METC/ITCTransmission): ~8,700 circuit miles at 120-345 kV.

## 2. Generation
- Historic mix (older Fermi 3 COLA environmental report): coal ~57%, gas ~23%,
  oil ~11%, nuclear ~9%. Much has changed since; use current filings.
- Current direction: coal retirement by 2032-2035, 1,300 MW coal-to-gas
  conversions (Monroe, Belle River), Fermi 2 nuclear retained and uprated,
  large solar/wind buildout, and a proposed 2042 renewable plan that converts
  coal sites to solar and wind.
- Production cost has fallen below retail: MISO/Michigan LCOE for new solar and
  wind is far under DTE's residential retail rate, which is why the retail-
  wholesale spread funds delivery, maintenance, and capital programs.
- Practical imported-power cost proxy for modeling: $35-55/MWh (3.5-5.5 c/kWh)
  for energy, plus capacity and ancillary costs; do not confuse with retail.

## 3. Transmission
- Voltage classes: 345 kV backbone (new MPSC-approved Nelson Road-Oneida
  39-mile double circuit, Gratiot-Eaton counties), 120-138 kV subtransmission,
  some 230 kV. New 345 kV segments and rebuilds are in active planning.
- Conductors: ACSR (Drake 795 kcmil and similar) at transmission; bundled
  conductors on high-capacity lines; OPGW or ADSS for fiber/communications.
- Right-of-way widths, clearances and EMF design follow IEEE/NESC and MPSC
  case practice; new lines are designed for lower field exposure than legacy.

## 4. Distribution
- Primary distribution: 13.2 kV and 4.8 kV. DTE runs "isolation downs" —
  4.8 kV circuits fed from 13.2 kV substations — extensively in Detroit and
  older suburbs (Royal Oak, Birmingham, Ann Arbor).
- The 4.8 kV system is the known weak point: aging cable, abandoned arc wire in
  Detroit (MPSC approved hardening funds), higher losses per kW delivered,
  limited ampacity, and constrained voltage regulation.
- Secondary: 120/240 V single phase residential; 208Y/120 and 480Y/277 V
  three-phase commercial/industrial.
- Transformers: substation GSUs (345/120, 120/13.2 kV) and pole-mount/pad-mount
  distribution transformers 15-500 kVA. Losses split roughly: no-load (core)
  ~0.5-1% of rating continuously, load (copper) losses scaling with I²R.
  DOE 2016+ efficiency standards apply; modern pole units run ~98.5-99% efficient
  at half load.
- Power conditioning on the feeder: switched capacitor banks (PF support),
  step-voltage regulators (LTC at substation + line regulators), reclosers and
  sectionalizers for fault isolation, fuses/arresters for lightning.

## 5. Delivery path A to B
Generator (~20 kV) -> GSU step-up to 345/120 kV -> transmission/subtransmission
-> substation transformer to 13.2 kV -> feeder (4.8/13.2 kV) -> distribution
transformer to 120/240 V -> service drop -> meter -> customer panel.
Each stage has losses: transmission 2-4%, distribution 4-6%, transformer
no-load losses a further 1-2% — so 8-12% of generated energy is lost in delivery.

## 6. Frequency and grid dynamics
- 60 Hz synchronous system; normal operating band 59.95-60.05 Hz, with wider
  disturbance excursions. NERC BAL-003 sets frequency-response obligations;
  MISO peak load is ~121 GW, which sets its reserve margin.
- Frequency deviates on loss of a large generator or block; UFLS relays shed
  load in steps (typically 59.3 Hz and down).
- For a customer, frequency is effectively 60 Hz at the meter; local effects
  come from harmonics (inverter/Motor drives) and transients, not bulk-system
  frequency.
- Harmonics: IEEE 519 sets THD limits (5% total voltage distortion at PCC);
  DER inverters must meet IEEE 1547 ride-through and power-quality clauses.

## 7. Smart meters and interval data
- DTE deployed AMI (Itron/Sensus-class) across the territory; billing reads are
  remote. Customers can obtain interval data through the DTE account portal and
  the Green Button standard (XML or CSV), commonly 15-minute or hourly intervals.
- Tool input: export "usage" or "interval" CSV from the portal, map the columns
  (timestamp, kWh or kW, optional kVar, voltage), then run grid_analyzer.py.
- Data quality notes: DTE meter intervals occasionally have gaps or estimated
  reads; treat missing intervals as null, not zero, when computing peaks.
## 8. Billing structure (residential and commercial)
- Michigan deregulates supply: DTE delivers, and customers may take DTE supply or
  an alternative supplier. Bills split into supply (energy) + delivery
  (distribution) + surcharges/riders.
- Residential: recently ~$8.50 fixed plus ~18.4 c/kWh (D1.11 TOU), with the
  standard rate around 20.05 c/kWh (Oct-May) and ~23.7 c/kWh all-in observed at
  500 kWh in April 2026. Time-of-day "Savers" rate 11.74 c/kWh off-peak.
- Typical distribution charge line items seen in DTE rate books: 9.726 c/kWh
  distribution plus a 6.670 c/kWh component on certain schedules.
- Commercial/industrial: demand charges per kW (or kVA) of billing demand plus
  energy, with ratchets for peak months; power-factor clauses apply above a
  threshold (typically 0.95). A $474M rate-hike request (pending) would raise
  residential bills by roughly 8-12%.
- Modeling defaults used by our tool (Michigan/DTE preset): energy $0.237/kWh,
  demand $20/kW-month, kVA-demand $12/kVA-month, PF threshold 0.95,
  CO2 0.42 kg/kWh (MISO Michigan mix, coal+gas+nuclear+renewables).

## 9. Cost stack: production, delivery, maintenance
- Production: fuel plus O&M, today ~$35-60/MWh blended; nuclear lowest marginal
  cost, gas sets the marginal price most hours, coal fading.
- Delivery: capital-heavy; substation and line investments recovered through
  distribution rates; per-kWh distribution charges above are the visible part.
- Maintenance: vegetation management is the largest recurring line item (nearly
  half of some utilities' distribution O&M), plus storm restoration, pole
  inspection/replacement, transformer and regulator servicing.
- Reliability reporting: MPSC requires SAIDI/SAIFI for the worst-performing
  circuits. DTE claims a ~70% reduction in outage time in 2024 versus prior
  years; independent audits of storm response (2025) remain critical of
  maintenance practices.

## 10. Weak points (what to look for in data)
- 4.8 kV legacy circuits: voltage sag, high losses, arc-wire hazards.
- Aging underground cable and PILC splices failing under moisture.
- Transformer loading above nameplate in summer peaks; ANSI loading guides
  permit short overloads but accelerate insulation aging.
- Long single-phase laterals with high impedance and poor fault detection.
- Storm exposure: ice and wind loading (NESC districts), tree contact, flooding
  of vaults and manholes.
- DER reverse flow on feeders designed for one-way flow; coordination of
  inverter ride-through with reclosers.
- Neutral/grounding problems producing stray voltages and EMF anomalies.
- Residential AMI data cannot see these directly, but load factor, PF, idle
  share, voltage spread and harmonics are the proxy signals our tool uses.

## 11. Environmental effects on the system
- Thermal rating: conductors derate with ambient temperature, solar gain and
  wind speed (IEEE 738); a calm 35 C day can cut ampacity 15-25%.
- Ice and wind: adds static load and galloping; ice shedding causes conductor
  slap and flashovers.
- Rain and pollution: corona loss and audible noise rise; insulators flash over
  when contaminated.
- Soil: resistivity drives grounding; dry seasons raise ground resistance and
  stray voltage.
- Lightning: direct strikes on laterals (arresters, shield wire).
- Heat: transformer aging roughly doubles per 6-8 C above rated hot-spot.

## 12. EMI, EMF and electrostatics
- Power-frequency fields: 60 Hz electric field under a 345 kV line ~1-5 kV/m at
  ground; magnetic field typically 0.1-10 µT under distribution, up to ~30 µT
  close to high-current lines. ICNIRP 2010 general-public reference levels:
  5 kV/m and 200 µT (50/60 Hz) — normal utility exposures sit far below these.
- Switched-mode harmonics from inverters and VFDs raise high-frequency
  emissions; IEEE 519 and FCC Part 15 (for equipment) bound them.
- Power-line carrier (PLC) and smart-meter mesh radios (900 MHz, 2.4 GHz) are
  separate from 60 Hz fields and are low-power.
- Electrostatics: induced voltage on fences and vehicles near HV lines; grounded
  shielding and signage required. Stray voltage investigations (milking parlors,
  pools) are a recognized utility service line.
- Measurement: gaussmeters (EMDEX, NARDA) for fields; power-quality analyzers
  (Fluke 1770, Hioki PW3198) for harmonics, sags, transients.

## 13. How the tool uses this pack
- `grid_analyzer.py --tariff dte` applies the §8 defaults (energy, demand, PF,
  CO2) so recommendations come out in Michigan dollars.
- Interval CSV from DTE's portal goes straight in; timestamp plus kWh (or kW)
  is enough for load factor, peak demand, idle share and PF arithmetic.
- Waveform captures (oscilloscope/logged samples) feed the harmonic path with
  `--fs` and `--f0 60`.
- Recommendations are hypotheses until measurement (M&V) confirms them.

## 14. Sources (checked Nov 2 2026)
- DTE rate options page: 20.05 c/kWh standard, Savers 11.74 c/kWh.
- ashbornpartners.com DTE 2026 analysis: $118.49 for 500 kWh = 23.70 c/kWh (Apr 2026).
- energypros.io: 22.72 c/kWh all-in; Detroit 20.25 c/kWh.
- DTE rate books (D1.11 TOU: $8.50 fixed + 18.4 c/kWh; 9.726 + 6.670 c/kWh
  distribution components).
- MPSC news releases: 345 kV Nelson Road-Oneida approval; 4.8 kV hardening funds.
- ITC/METC statistics: 8,700 circuit miles, 120-345 kV.
- Fermi 3 COLA environmental report: historic fuel mix.
- DTE IRP filings and 2042 renewable plan coverage: coal exit, conversions.
- ACEEE smart-meter-data paper; Green Button standard documentation.
- ICNIRP 2010 guidelines (1 Hz-100 kHz), public reference levels.
