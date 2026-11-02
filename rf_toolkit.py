#!/usr/bin/env python3
"""RF Toolkit: frequency-engineering primitives, stdlib only (no numpy).

Covered per the research brief: generation (modulation), detection (envelope
detector, FFT), shaping (windowed-sinc FIR), amplification control (AGC),
squelch (hysteresis gate), rectification, synchronization (cross-correlation),
compression (mu-law companding), beamforming (ULA steering, array factor,
beamwidth), spectral measurement (occupied bandwidth, centroid, SNR, EVM),
and interference analysis (intermodulation products vs a band plan).

Every function is deterministic. Run `python3 rf_toolkit.py` for the selftest.
"""
import cmath
import math
import random

# ---------------------------------------------------------------- spectrum

def fft(x):
    """Recursive radix-2 Cooley-Tukey FFT. Length must be a power of 2."""
    n = len(x)
    if n & (n - 1):
        raise ValueError("length must be a power of 2")
    if n <= 1:
        return [complex(v) for v in x]
    even = fft(x[0::2])
    odd = fft(x[1::2])
    out = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * odd[k]
        out[k] = even[k] + t
        out[k + n // 2] = even[k] - t
    return out


def spectrum_db(signal, fs):
    """Return (freqs, magnitudes_dB) for a signal sampled at fs Hz."""
    n = 1
    while n < len(signal):
        n <<= 1
    buf = list(signal) + [0.0] * (n - len(signal))
    x = fft(buf)
    half = n // 2
    freqs = [k * fs / n for k in range(half)]
    mags = [abs(v) / (n / 2) for v in x[:half]]
    return freqs, [20 * math.log10(m + 1e-12) for m in mags]


def peak_freq(signal, fs):
    """Dominant frequency in Hz."""
    freqs, db = spectrum_db(signal, fs)
    i = max(range(len(db)), key=lambda k: db[k])
    return freqs[i]


def occupied_bandwidth(signal, fs, fraction=0.99):
    """Bandwidth (Hz) containing `fraction` of total power.

    Expands outward from the peak bin, adding bins in order of distance, until
    the captured power reaches the requested fraction. Robust for a pure tone
    (where one bin dominates) and for wideband signals alike.
    """
    freqs, db = spectrum_db(signal, fs)
    power = [10 ** (v / 10) for v in db]
    total = sum(power)
    peak = max(range(len(power)), key=lambda i: power[i])
    lo = hi = peak
    acc = power[peak]
    while acc < total * fraction and (lo > 0 or hi < len(power) - 1):
        take_left = lo > 0 and (hi >= len(power) - 1 or power[lo - 1] >= power[hi + 1])
        if take_left:
            lo -= 1
            acc += power[lo]
        else:
            hi += 1
            acc += power[hi]
    return freqs[hi] - freqs[lo]


def spectral_centroid(signal, fs):
    """Power-weighted mean frequency (Hz)."""
    freqs, db = spectrum_db(signal, fs)
    power = [10 ** (v / 10) for v in db]
    return sum(f * p for f, p in zip(freqs, power)) / sum(power)

# ---------------------------------------------------------------- metrics

def snr_db(clean, noisy):
    """SNR in dB given a clean reference and its observed version."""
    sig = sum(v * v for v in clean)
    noise = sum((a - b) ** 2 for a, b in zip(clean, noisy))
    return 10 * math.log10(sig / max(noise, 1e-30))


def evm_pct(ideal, received):
    """Error-vector magnitude as a percentage of ideal constellation power."""
    err = sum(abs(r - i) ** 2 for i, r in zip(ideal, received))
    ref = sum(abs(i) ** 2 for i in ideal)
    return 100.0 * math.sqrt(err / ref)

# ---------------------------------------------------------------- generation

def am_modulate(message, fc, fs, depth=0.8):
    """Amplitude modulation. message in [-1,1], one sample per message sample."""
    return [(1 + depth * m) * math.sin(2 * math.pi * fc * k / fs)
            for k, m in enumerate(message)]


def fm_modulate(message, fc, fs, deviation):
    """Frequency modulation with peak deviation (Hz)."""
    phase, out = 0.0, []
    for s in message:
        phase += 2 * math.pi * (fc + deviation * s) / fs
        out.append(math.sin(phase))
    return out


def constellation(scheme, n=400):
    """Ideal complex symbols for bpsk/qpsk/16qam."""
    rng = random.Random(7)
    if scheme == "bpsk":
        return [complex(rng.choice((1, -1)), 0) for _ in range(n)]
    if scheme == "qpsk":
        s = 1 / math.sqrt(2)
        return [complex(rng.choice((s, -s)), rng.choice((s, -s))) for _ in range(n)]
    if scheme == "16qam":
        levels = (-3, -1, 1, 3)
        return [complex(rng.choice(levels), rng.choice(levels)) / 3.0 for _ in range(n)]
    raise ValueError("scheme must be bpsk, qpsk or 16qam")


def add_awgn(symbols, snr_db_level, seed=11):
    """Add complex AWGN at the given SNR."""
    rng = random.Random(seed)
    power = sum(abs(s) ** 2 for s in symbols) / len(symbols)
    sigma = math.sqrt(power / (2 * 10 ** (snr_db_level / 10)))
    return [s + complex(rng.gauss(0, sigma), rng.gauss(0, sigma)) for s in symbols]

# ---------------------------------------------------------------- shaping / filtering

def fir_lowpass(cutoff, taps, fs):
    """Hamming-windowed sinc lowpass, DC-normalised. cutoff in Hz."""
    m = taps - 1
    h = []
    for i in range(taps):
        n = i - m / 2
        sinc = 1.0 if n == 0 else math.sin(2 * math.pi * cutoff / fs * n) / (math.pi * n)
        h.append(sinc * (0.54 - 0.46 * math.cos(2 * math.pi * i / m)))
    gain = sum(h)
    return [v / gain for v in h]


def convolve(signal, taps):
    """Direct convolution, 'same'-length output."""
    out = []
    for i in range(len(signal)):
        acc = 0.0
        for j, h in enumerate(taps):
            k = i - j
            if 0 <= k < len(signal):
                acc += signal[k] * h
        out.append(acc)
    return out

# ---------------------------------------------------------------- gain / gating

def envelope_detect(signal, taps=9):
    """Rectify then smooth: the classic envelope detector."""
    return convolve([abs(v) for v in signal], [1.0 / taps] * taps)


def agc(signal, target_rms=0.5, rate=0.05):
    """Gain control toward a target RMS; returns (output, final_gain)."""
    gain, out = 1.0, []
    for v in signal:
        out.append(v * gain)
        rms = abs(v) or 1e-9
        gain += rate * (target_rms / rms - gain) * 0.01
    return out, gain


class Squelch:
    """Hysteresis gate: opens at `threshold_db`, closes below `threshold_db - hysteresis`."""

    def __init__(self, threshold_db=-40.0, hysteresis=3.0):
        self.threshold_db = threshold_db
        self.hysteresis = hysteresis
        self.open = False

    def update(self, power_db):
        if self.open and power_db < self.threshold_db - self.hysteresis:
            self.open = False
        elif not self.open and power_db >= self.threshold_db:
            self.open = True
        return self.open

# ---------------------------------------------------------------- sync

def cross_correlate(a, b):
    """Normalised cross-correlation; returns (best_lag, peak_value)."""
    best_lag, best = 0, -2.0
    for lag in range(-(len(a) - 1), len(b)):
        acc = norm_a = norm_b = 0.0
        for i in range(len(a)):
            j = i + lag
            if 0 <= j < len(b):
                acc += a[i] * b[j]
                norm_a += a[i] ** 2
                norm_b += b[j] ** 2
        if norm_a and norm_b:
            score = acc / math.sqrt(norm_a * norm_b)
            if score > best:
                best_lag, best = lag, score
    return best_lag, best

# ---------------------------------------------------------------- compression

def mulaw_encode(x, mu=255.0):
    """ITU G.711 mu-law companding of x in [-1,1]."""
    sign = 1.0 if x >= 0 else -1.0
    return sign * math.log1p(mu * abs(x)) / math.log1p(mu)


def mulaw_decode(y, mu=255.0):
    """Inverse of mulaw_encode."""
    sign = 1.0 if y >= 0 else -1.0
    return sign * ((1 + mu) ** abs(y) - 1) / mu

# ---------------------------------------------------------------- beamforming

def ula_steering(n_elements, spacing_lambda, angle_rad):
    """Steering vector for a uniform linear array."""
    return [cmath.exp(-2j * math.pi * spacing_lambda * k * math.sin(angle_rad))
            for k in range(n_elements)]


def array_factor(n_elements, spacing_lambda, scan_rad, angle_rad):
    """Normalised array-factor magnitude for a scanned ULA."""
    w = [complex(v).conjugate() for v in ula_steering(n_elements, spacing_lambda, scan_rad)]
    a = ula_steering(n_elements, spacing_lambda, angle_rad)
    return abs(sum(wi * ai for wi, ai in zip(w, a))) / n_elements


def beamwidth_deg(n_elements, spacing_lambda):
    """Approximate -3 dB beamwidth (degrees) of a ULA by scanning."""
    peak = 1.0
    lo = hi = 0.0
    step = 0.05
    ang = 0.0
    while ang < 90:
        val = array_factor(n_elements, spacing_lambda, 0.0, math.radians(ang))
        if val >= peak * 0.707:
            hi = ang
        ang += step
    ang = 0.0
    while ang > -90:
        val = array_factor(n_elements, spacing_lambda, 0.0, math.radians(ang))
        if val >= peak * 0.707:
            lo = ang
        ang -= step
    return hi - lo

# ---------------------------------------------------------------- interference

def imd_products(f1, f2, order=3):
    """Intermodulation products up to `order` for two tones (MHz units kept)."""
    out = set()
    for m in range(1, order + 1):
        for n in range(1, order + 1):
            if 2 <= m + n <= order:
                out.add(round(m * f1 - n * f2, 3))
                out.add(round(n * f2 - m * f1, 3))
    return sorted(v for v in out if 0 < v < 5 * max(f1, f2))


def check_imd(tx_freqs, band_start, band_end, order=3, guard_pct=1.0):
    """Flag intermodulation products that land inside a protected band."""
    hits = []
    for i in range(len(tx_freqs)):
        for j in range(i + 1, len(tx_freqs)):
            for p in imd_products(tx_freqs[i], tx_freqs[j], order):
                guard = (band_end - band_start) * guard_pct / 100.0
                if band_start - guard <= p <= band_end + guard:
                    hits.append({"tones": (tx_freqs[i], tx_freqs[j]), "product": p})
    return hits

# ---------------------------------------------------------------- selftest

def selftest():
    fs = 8000
    tone = [math.sin(2 * math.pi * 1000 * k / fs) for k in range(1024)]
    assert abs(peak_freq(tone, fs) - 1000) < 40, peak_freq(tone, fs)
    assert 900 < spectral_centroid(tone, fs) < 1100
    # A pure tone occupies one bin (bandwidth 0 by construction); a two-tone
    # signal is genuinely spread, so it must show a real occupied bandwidth.
    two_tone = [math.sin(2 * math.pi * 1000 * k / fs) + math.sin(2 * math.pi * 1200 * k / fs)
                for k in range(1024)]
    bw = occupied_bandwidth(two_tone, fs)
    assert 150 < bw < 350, bw
    rng = random.Random(3)
    noisy = [v + rng.gauss(0, 0.1) for v in tone]
    assert 15 < snr_db(tone, noisy) < 30
    ideal = constellation("qpsk")
    assert evm_pct(ideal, ideal) < 1e-9
    assert evm_pct(ideal, add_awgn(ideal, 20)) < 20
    msg = [math.sin(2 * math.pi * 50 * k / fs) for k in range(400)]
    assert len(am_modulate(msg, 1000, fs)) == 400
    assert len(fm_modulate(msg, 1000, fs, 200)) == 400
    h = fir_lowpass(500, 31, fs)
    assert abs(sum(h) - 1.0) < 1e-6
    dc = convolve([1.0] * 100, h)
    assert abs(dc[-1] - 1.0) < 0.02
    env = envelope_detect([math.sin(2 * math.pi * 100 * k / fs) for k in range(400)])
    assert max(env) > 0.5
    out, g = agc([0.01] * 200)
    assert out[-1] > out[0]
    sq = Squelch(-20)
    assert not sq.update(-40)
    assert sq.update(-10)
    assert sq.update(-21)          # inside hysteresis band, stays open
    assert not sq.update(-30)      # below threshold - hysteresis, closes
    lag, peak = cross_correlate([1, 2, 3, 4], [0, 0, 1, 2, 3, 4, 0])
    assert lag == 2 and peak > 0.99, (lag, peak)
    for x in (-0.9, -0.3, 0.0, 0.5, 0.95):
        assert abs(mulaw_decode(mulaw_encode(x)) - x) < 0.01
    af0 = array_factor(8, 0.5, 0.0, 0.0)
    af30 = array_factor(8, 0.5, 0.0, math.radians(30))
    assert af0 > 0.99 and af30 < 0.3, (af0, af30)
    assert 0 < beamwidth_deg(8, 0.5) < 40
    prods = imd_products(1000, 1010, 3)
    assert any(abs(p - 990) < 1e-6 for p in prods), prods
    assert check_imd([1000, 1010], 985, 995)           # 3rd order lands in band
    print("rf_toolkit selftest: 18/18 checks passed")


if __name__ == "__main__":
    selftest()
