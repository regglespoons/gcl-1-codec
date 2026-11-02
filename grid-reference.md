# Grid & Power-Electronics Reference

Companion to `grid_analyzer.py`. Covers what the tool measures, the control
modes people argue about, what belongs in software versus on site, the
standards that govern it, and the realistic career path.

## 1. What "weak points" actually means in a distribution system

Measured weaknesses, each with the instrument that proves it:

| Weak point | Evidence | Typical instrument |
|---|---|---|
| Low power factor (<0.95) | kVA demand above kW; PF penalties | PQ analyzer at service entrance |
| Poor load factor (<0.45) | peak >> mean across intervals | AMI/interval data, utility portal |
| Idle/standby load | baseload persists when production stops | submetering |
| Voltage sag/swell (>8% spread) | voltage spread across intervals | Class A PQ logger |
| Harmonics (THD >5% at PCC) | 5th/7th/11th rise from drive loads | waveform capture + FFT |
| Phase imbalance (>10%) | neutral current, negative sequence | 3-phase logger |
| Passive intermodulation | new tones from mixed high-power signals | PIM tester at connectors |
| Peak demand charges | top 15-min interval sets the monthly bill | interval data + tariff |

Software can find all of these from data. It cannot measure what nobody
instrumented, and it cannot change a transformer tap remotely.

## 2. The modulation/control vocabulary, made precise

People say these loosely. What each one actually is, and where it wins:

- **PWM** (pulse-width modulation): fixed switching frequency, variable duty
  cycle. The default above ~20% load. Losses: switching ∝ fsw, conduction ∝ I².
- **PFM** (pulse-frequency modulation): constant on-time, variable frequency.
  Wins at light load because switching events drop with the load. Common in
  small DC/DC and in standby rails.
- **PSM / burst / pulse-skip**: gate cycles off entirely. Wins below ~5-10%
  load where even PFM overhead dominates. Costs ripple and EMI.
- **Phase-shifted PWM (PS-PWM)**: N interleaved phases offset by Ts/N. Ripple
  cancels at N×fsw; standard in multiphase buck/boost and in inverter bridges.
- **Multiphase PWM with phase shedding**: reduce active phase count as load
  falls so each remaining phase stays in its efficient current band. This is
  the single biggest light-load win in server and EV chargers.
- **SVPWM** (space-vector PWM): three-phase variant that maximizes DC-bus
  utilization (~15% over sinusoidal PWM) and lowers harmonic distortion.
- **Hysteretic / bang-bang**: simplest, fastest, variable frequency. Fine for
  the right loads; bad EMI citizenship at high power.
- **Peak current-mode / average current-mode**: inner current loop shapes the
  waveform (what a PFC stage uses so line current follows line voltage).
- **MPPT** (perturb & observe, incremental conductance): solar and energy
  harvesting only; it is a tracking algorithm, not a modulation.
- **Droop control**: grid-forming inverters share load by frequency/voltage
  droop; relevant the moment you touch storage or islanded operation.
- **Dead time**: not modulation, but the thing that eats efficiency and
  generates distortion in every half-bridge. 100-200 ns typical; too much
  costs THD, too little risks shoot-through.

Terms like "PhWM"/"PWWM" bounce around; nearly always they mean phase-shifted
or multiplexed PWM. Ask what the switching frequency and phase count are, and
the ambiguity dissolves.

## 3. Software versus on-site (the honest split)

Software, from data alone:
- interval-data analysis, load-factor and demand-charge math
- harmonic THD and per-order content from waveform captures
- PFC sizing, filter sizing, transformer derating
- ranked recommendations with dollar and CO₂ estimates
- control code generation (duty tables, phase-shedding thresholds, schedules)
- report generation for the customer

On site, with authorization:
- power-quality logging at the PCC, CT/VT installation
- confirming nameplate and as-built against design
- PIM tests, thermography, sweep of capacitor banks
- firmware/hardware changes and commissioning
- anything touching the utility's equipment (their crew, their rules)

## 4. Standards that govern the recommendations

- **IEEE 519**: harmonic limits at the point of common coupling (5% THD planning level).
- **IEEE 1547**: interconnection of distributed resources (inverters, storage).
- **IEC 61000-3-2 / -3-12**: harmonic current emissions by equipment class.
- **EN 50160**: voltage characteristics of supplied electricity (European benchmark).
- **NEC article 220 / 690 / 705**: load calc, solar, interconnection.
- **UL 1741 (SB)**: inverter listing for grid support functions.
- **47 CFR 15**: unintentional radiators, i.e. your switching supply's EMI.
- **NFPA 70E**: arc-flash safety before anyone opens a panel.

## 5. Where the savings actually come from (typical ranges)

- Power-factor correction: 1-4% of the bill where kVA demand or penalties apply.
- Demand-charge management: 5-15% for spiky loads with battery or scheduling.
- Idle/standby elimination: 2-8% in facilities running 24/7 at low utilization.
- Drive/motor efficiency (VFD where throttling was used): 10-30% on fan/pump energy.
- Harmonic mitigation: mostly avoided failures and derating, not direct energy.
- Phase shedding in new designs: 1-3% at light load, more in data centers.

Claims outside these bands need measurement to back them.

## 6. Equipment and software ecosystem

- **Meters/loggers**: Fluke 1770 series, Hioki PQ3198, Accuenergy Acuvim,
  Schneider PowerLogic, Janitza UMG, Dranetz.
- **Current transformers**: split-core (retrofit) vs solid-core (accuracy);
  class 0.2 for revenue, 1.0 for analysis.
- **Submetering**: Accuenergy, Dent, Schneider; Modbus/BACnet backends.
- **Simulation**: PLECS, PSIM, LTspice, MATLAB/Simulink, OpenModelica.
- **Open source**: ngspice, OpenDSS (distribution planning), pandapower,
  PyPSA (grid optimization), scikit-rf (RF side), GNU Radio (RF side).
- **Analysis**: pandas + this toolkit; Grafana for dashboards once data flows.
- **Control prototyping**: TI C2000 (the industry default for digital power),
  STM32G4, Zephyr RTOS, Simulink code generation.

## 7. Career path (realistic, in order)

1. **Energy analyst** at an ESCO, utility, or facilities team: owns interval
   data, finds savings, writes the recommendations. Entry point; no license.
2. **Commissioning / M&V technician**: proves the savings after installation
   (IPMVP protocols). Certifications: CEM (AEE), CEA, or utility programs.
3. **Power-quality consultant**: PQ logging, harmonic studies, PIM hunting.
   Tools above; report writing is half the job.
4. **Power electronics engineer**: designs the converters. Needs EE degree
   plus lab time; C2000 experience is the differentiator.
5. **Professional Engineer (PE, power)**: the stamp that lets you sign designs
   and interconnection studies. Requires FE exam + supervised experience.

Sellable service, today, with this tool: interval-data audit → ranked savings
memo → optional follow-up measurement. That is exactly how small consultancies
start, and it pairs with the planetary goal: every kWh not burned is real.

## 8. Legal boundaries (non-negotiable)

- Never touch, tune, or transmit into utility or third-party equipment without
  written authorization from the operator; licensed spectrum and grid assets are
  regulated.
- Do not claim measured savings without measurement; IVMVP/M&V exists because
  optimistic estimates destroy credibility.
- Arc-flash and lockout/tagout rules apply before any panel is opened.
- Grid-modifying equipment must be listed (UL 1741) and interconnected per
  IEEE 1547 and the utility's tariff.

## 9. Using the analyzer

```
python3 grid_analyzer.py selftest              # 14 checks
python3 grid_analyzer.py demo                  # synthetic site, full report
python3 grid_analyzer.py analyze site.csv      # your interval data (needs a kw column)
python3 grid_analyzer.py wave capture.csv --fs 15360 --f0 60   # THD from a waveform
```

CSV headers are matched loosely: `kw` required; `kvar`, `voltage`, `pf` optional.

Output: metrics, weak points with evidence, ranked remedies with annual
dollars and CO₂, then control code (PFC sizing, phase shedding, mode
selection, load schedule) parameterized with the site's own numbers.
