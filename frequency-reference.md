# Frequency Engineering Reference
Comprehensive notes for the frequency-lab toolkit (compiled Nov 1 2026).

## 1. Spectrum map and propagation

| Band | Range | Character | Typical use |
|---|---|---|---|
| ELF/SLF | 3 Hz - 30 kHz | Ground/water penetration, tiny bandwidth | Submarine comms, geology |
| VLF/LF | 30 kHz - 300 kHz | Global groundwave, time signals | Navigation (LORAN), WWVB |
| MF | 300 kHz - 3 MHz | D-layer absorption by day, skywave at night | AM broadcast (530-1700 kHz) |
| HF | 3 - 30 MHz | Ionospheric skywave, long range, unreliable | Shortwave, aviation, amateur |
| VHF | 30 - 300 MHz | Line of sight, terrain-sensitive | FM broadcast (88-108), air band, marine |
| UHF | 300 MHz - 3 GHz | LOS, penetration tradeoffs | TV, cellular 600/700/850, land mobile |
| SHF | 3 - 30 GHz | Rain/foliage loss, high gain antennas | Wi-Fi, 5G mid-band, Ku/Ka satcom |
| EHF | 30 - 300 GHz | Severe atmospheric loss, short range | 5G mmWave, 60 GHz WiGig, radar |
| THz | 0.1 - 10 THz | Research, near-optical | 6G studies, spectroscopy |

Propagation essentials: Friis transmission (Pr = Pt*Gt*Gr*(lambda/4*pi*d)^2), free-space path loss rises 20 dB per decade of distance and 20 dB per decade of frequency; Fresnel zone clearance for LOS links; knife-edge diffraction; multipath and fading (Ricean/Rayleigh); rain fade above ~10 GHz scales with GHz and rainfall rate.

## 2. The transmit and receive chain

Tx: baseband DSP -> DAC -> upconverter (LO mixing) -> driver -> PA (or Doherty/ET stage) -> filters/duplexer -> antenna.
Rx: antenna -> LNA -> downconverter -> ADC -> DSP.

Key figures of merit:
- EIRP = Ptx + Gant - losses. Regulatory caps per service; e.g. Starlink Mini user terminal filings cite peak EIRP around 39.2 dBW; Ku/Ka NGSO systems operate under PFD/EPFD limits (see FCC DA-24-222A1 for Ku/Ka sharing rules and the 18.6-19.7 GHz PFD limits where EPFD does not apply).
- PFD = power flux density at Earth's surface; EPFD = equivalent PFD aggregated across a constellation. These are the levers regulators use for satellite/terrestrial coexistence.
- G/T (receive figure of merit), noise figure, sensitivity: minimum detectable signal ~ kTB + NF + required SNR.
- IP3/P1dB: linearity budget; ACPR and spectral-emission masks constrain PA backoff.
- Dynamic range: ADC bits vs strong-signal blocking; AGC placement matters.

## 3. Emission bandwidth

Necessary vs occupied bandwidth; emission designators (e.g. 16K0F3E: 16.0 kHz, FM telephony). Spectral masks (FCC Part 90/95, 3GPP SEM) define the shoulders. Filter before the PA to prevent splatter; cavity filters and combiners at shared tower sites prevent adjacent-channel and co-site interference.

## 4. Modulation, shaping, conversion

- Analog: AM (carrier + sidebands, 2x bandwidth), FM (Carson's rule: BW = 2*(deviation + modulating freq)), SSB.
- Digital linear/nonlinear: ASK, FSK/GMSK, BPSK/QPSK/16-256QAM, OFDM (high PAPR, susceptible to frequency offset), SC-FDMA (lower PAPR), DFT-s-OFDM in 5G uplink.
- Spread: DSSS and FHSS; chirp (LoRa) coding.
- Shaping: root-raised-cosine pulse shaping limits occupied bandwidth; crest-factor reduction (CFR) and digital predistortion (DPD) linearize the PA and cut ACPR by 10-20 dB.
- Conversion/inversion: up/down conversion by LO mixing, image rejection, IQ imbalance correction; frequency inversion is just a spectral mirror - useful in scrambling and in some analytics, not a compression.

## 5. Amplification and stabilization

Classes A (linear, inefficient), AB (broadcast standard), C (FM constant-envelope), Doherty (efficiency at backoff, LTE/5G macros), envelope tracking. Thermal design, bias stability, gain flatness across the band, group-delay variation. Stabilize with temperature-compensated references (TCXO/OCXO) and AGC loops.

## 6. Antennas and beamforming

Antenna gain vs beamwidth tradeoff; downtilt (mechanical vs electrical) controls cell-edge interference; sectorization (3x120 deg typical). MIMO and massive MIMO exploit spatial multiplexing.

Uniform linear array math (implemented in rf_toolkit.py): steering vector a(theta)_k = exp(-j*2*pi*d*k*sin(theta)), weights w = a(scan)^H, array factor |w^H a(theta)|; -3 dB beamwidth narrows with element count; grating lobes appear when element spacing exceeds 0.5 lambda. Beamforming gains scale with N elements for the main lobe; sidelobe suppression requires windowing (Chebyshev/Taylor).
Ergodic notes for the service pitch: real deployments use phase-coherent arrays with calibration; passive beamforming via reflectors (RIS) and digital beamforming in baseband.

## 7. Synchronization

GPS/GNSS timing (PRTC) provides 1 pps and UTC; PTP/IEEE 1588v2 carries time over packet networks; TDD and 5G NR require phase alignment (typically ~1.5 us for FR1, tighter for advanced features). Holdover oscillators (OCXO/Rb) cover GNSS outages. Clock jitter degrades EVM and phase noise; measure with phase-noise analyzers.

## 8. Detection, squelch, gating

Envelope detection, FFT channelizers, energy detectors, matched filters, cyclostationary detection for signal identification. Squelch gates audio when carrier drops below threshold with hysteresis to prevent chatter (implemented in rf_toolkit.py Squelch). RSSI/RSRP/RSRQ are the cellular measurement set.

## 9. Compression in the RF chain

Baseband transport compression: CPRI/eCPRI line rates, IQ sample compression, mu-law companding (G.711) for voice, crest-factor reduction, and lossy spectral quantization. Audio/video compression is a separate domain (see audio-video-codecs.md).

## 10. Frequency planning and interference

Channel plans with guard bands; co-channel vs adjacent-channel; intermodulation products: for tones f1, f2 the 3rd-order products 2f1-f2 and 2f2-f1, 5th-order 3f1-2f2 etc. (rf_toolkit.imd_products/check_imd). Passive intermodulation (PIM) at connectors, jumpers, and rusty hardware is a top field problem at shared sites - test with a PIM analyzer (2x43 dBm standard). Harmonics, image frequencies, and LO leakage; IF plan design to move images out of band.

## 11. Current spectrum status (verified Nov 2026)

- WRC-27 will decide new IMT identifications; studies target the 7-8.5 GHz range (upper mid-band / FR3). Candidate slices discussed include 4.4-4.8 GHz, 7.125-7.25 GHz, and 10-10.5 GHz. 6G work assumes roughly 400 MHz of new mid-band per market.
- 5G mmWave bands: n257 (28 GHz), n258 (26 GHz), n260 (39 GHz), n261 (28 GHz US).
- Starlink Ku-band user link: downlink 10.7-12.7 GHz, uplink 14.0-14.5 GHz; Ka-band gateway and user bands in 17.8-20.2 GHz (down) and 27.5-30 GHz (up) ranges, governed by PFD/EPFD limits and EIRP caps in FCC filings.
- Wi-Fi: 2.4/5/6 GHz (Wi-Fi 6E/7), 60 GHz (WiGig).

## 12. Equipment and software ecosystem

- SDRs: Ettus USRP, Analog Devices Pluto, HackRF One, RTL-SDR (receive only), LimeSDR, bladeRF.
- Instruments: spectrum analyzers (R&S FSW, Keysight N9020B), vector network analyzers, signal generators (R&S SMBV, Keysight MXG), power meters, PIM analyzers, drive-test scanners.
- Simulation/design: Ansys HFSS, CST Studio, Keysight ADS, MATLAB/Simulink, open-source GNU Radio + gr-osmosdr, SDR#, SigMF for IQ recording, SatDump for satellite decoding.
- Network planning: Atoll, Planet, Mentum, and vendor tools (Ericsson/Nokia/Huawei planning suites).

## 13. Legal and service framing (must-read)

- 47 CFR 333 (and parallel rules) prohibit jamming or interfering with authorized radio communications. Operating on, or "optimizing," spectrum you are not licensed for is unlawful regardless of intent. Unlicensed operation is limited to Part 15/95 rules (power, duty cycle, band).
- Optimizing a third party's broadcast, cellular, or satellite equipment requires their authorization and, in practice, licensed/credentialed engineers (PE where required). Commercial engagements: RF site audits, coverage and interference measurement, PIM testing, antenna tilt/azimuth optimization, spectrum-clearing studies, EMC pre-compliance - all performed for and with the licensed operator.
- HAARP and DARPA are government research programs, not commercial customers. Legitimate engagement is via SBIR/STTR, GSA schedules, or prime contractors with proper clearances; unsolicited "optimization" outreach to them is not a viable or appropriate channel.
- EMC standards to cite in proposals: FCC Part 15/18, CISPR 11/22/32, IEC 61000 series, MIL-STD-461 for defense work.

## 14. What the toolkit provides

rf_toolkit.py (stdlib only, 18 self-tests): FFT spectrum, peak frequency, occupied bandwidth, spectral centroid, SNR, EVM, AM/FM generation, constellations (BPSK/QPSK/16QAM), AWGN, FIR lowpass design and convolution, envelope detection, AGC, squelch with hysteresis, cross-correlation sync, mu-law companding, ULA beamforming (steering, array factor, beamwidth), intermodulation product analysis. See README.md for usage.
