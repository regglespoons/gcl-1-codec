# Audio/Video Codecs, Recording, Editing, Analysis and Production
Reference for the analyzer feature and production work (compiled Nov 1 2026).

## 1. Video codecs

| Codec | Type | Typical bitrate (1080p30) | Notes |
|---|---|---|---|
| H.264/AVC | Interframe | 4-12 Mbps | Universal compatibility; browser default |
| H.265/HEVC | Interframe | 2-6 Mbps | ~50% better than H.264; patent pools; partial browser support |
| H.266/VVC | Interframe | 1.5-4 Mbps | ~40% better than HEVC; limited deployment as of 2026 |
| AV1 | Interframe | 2-5 Mbps | Royalty-free, strong for streaming; modern browsers |
| VP9 | Interframe | 3-8 Mbps | YouTube lineage; WebM |
| ProRes (422/422 HQ/4444) | Intra only | 220-700 Mbps | Editing intermediate; Apple ecosystem |
| DNxHR (SQ/HQ/HQX) | Intra only | 145-700 Mbps | Avid intermediate, cross-platform |
| MPEG-2 | Interframe | 15-25 Mbps | Legacy broadcast/ATSC; still in archives |
| Theora | Interframe | 6-10 Mbps | Legacy open codec |

Editing rule: transcode delivery codecs (H.264/5, AV1) to an intra-frame intermediate (ProRes/DNxHR) before heavy editing, or use proxies. Generation loss is real: never re-encode a delivery file more than necessary; cut from the highest-quality source available.

## 2. Audio codecs

| Codec | Bitrate | Latency | Notes |
|---|---|---|---|
| PCM (WAV/AIFF) | 1411 kbps stereo 16/44.1 | none | Editing and archive standard |
| FLAC/ALAC | 400-1000 kbps | low | Lossless compression |
| AAC-LC | 96-256 kbps | low | Universal delivery |
| AAC-HE/HEv2 | 32-64 kbps | low | Low-bitrate streaming |
| Opus | 6-510 kbps | very low | Best modern general-purpose; WebM/RTC |
| Vorbis | 96-256 kbps | low | Legacy WebM |
| MP3 | 128-320 kbps | low | Compatibility only |
| G.711 mu-law | 64 kbps | minimal | Telephony; algorithm in rf_toolkit.py |
| G.722/G.729 | 48-64 / 8 kbps | low | VoIP |

Loudness standards: EBU R128 (-23 LUFS broadcast), ATSC A/85 (-24 LKFS US television), -14 LUFS for streaming delivery targets. Peak true-peak ceiling -1 dBTP.

## 3. Containers

MP4/MOV (ISO BMFF) - delivery; MKV - flexible, subtitles; WebM - the web pair (VP9/AV1 + Opus/Vorbis); MXF - broadcast interchange; TS - transport stream, legacy broadcast; AVI - legacy.

## 4. Recording, editing and production software

- NLEs: DaVinci Resolve (free tier; grading + editing + Fairlight audio), Adobe Premiere Pro, Final Cut Pro, Avid Media Composer (broadcast standard), Vegas Pro, Lightworks, Shotcut, Kdenlive (open source).
- Recording/streaming: OBS Studio (screen + capture cards, NVENC/AMF/QSV encoders), vMix, Wirecast.
- Transcoding/compression: FFmpeg (the workhorse: -crf, -preset, -vf scale, loudnorm filter), HandBrake (GUI), Shutter Encoder.
- Audio production: Pro Tools, Logic Pro, Ableton Live, Reaper, Cubase, Audacity, Ardour; spectral repair: iZotope RX.
- Analysis: FFmpeg astats/ebur128, Spek (spectrograms), Youlean Loudness Meter, DaVinci scopes (waveform, vectorscope, histogram).
- Hardware: Blackmagic/AJA capture cards, Atomos recorders, calibrated monitors (Rec.709/2100), audio interfaces.

## 5. Compression practice

- Quality-targeted encoding: CRF (x264/x265 18-28 typical; SVT-AV1 20-35), vs bitrate-targeted CBR/VBR for live streaming.
- Bitrate ladder for streaming: 1080p30 5 Mbps, 720p30 2.5 Mbps, 480p30 1 Mbps, 360p 0.6 Mbps (H.264 reference points).
- Chroma subsampling 4:2:0 for delivery, 4:2:2 for broadcast editing, 4:4:4 for VFX and screen content.
- GOP length 2-10 s for VOD, 1-2 s for low-latency live; B-frames improve compression at cost of latency.
- HDR: PQ/HLG transfer functions, 10-bit minimum, Rec.2020 primaries.

## 6. Browser support relevant to the in-app analyzer

Decodable in the analyzer: MP4 with H.264+AAC (universal), WebM with VP8/VP9/AV1+Opus/Vorbis (modern browsers), WAV PCM (universal), some HEVC (Safari/Edge, Chrome with hardware support). Not decodable: ProRes, DNxHR, MXF, MPEG-2 TS, AVCHD - transcode to H.264/VP9/AV1 first (FFmpeg one-liner in README).

## 7. What the analyzer measures

Per sampled frame (10 across the clip at 160x90): mean luma, luma standard deviation (contrast), mean saturation, edge energy (Sobel-style gradient - sharpness/detail), and inter-frame motion. Audio: 250 ms RMS windows in dBFS with peak. Practical readings: luma below ~30 = underexposed, above ~225 = clipped; contrast below ~20 = flat/washed frame; edge energy spikes with sharp text or noise; motion 0 across all frames = static shot; audio peak above -1 dBFS = likely clipping; mean below -30 dBFS = quiet mix.
