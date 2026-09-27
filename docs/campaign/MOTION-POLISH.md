# Motion polish — v2

This revision uses HTML, SVG and GSAP in HyperFrames, with FFmpeg for the underlying picture and audio tracks. **It is not an Adobe After Effects render and does not include an After Effects project.** The motion reference informs the editing vocabulary; its name is not a claim that every suggested effect was implemented.

## Exact reference

The reference is [`anton-abyzov/vskill/motion-graphics-promo` version 1.1.0](https://github.com/anton-abyzov/vskill/blob/0a2430fa4cd324090dd9edf737a542fa7154e2aa/skills/motion-graphics-promo/SKILL.md), pinned to commit `0a2430fa4cd324090dd9edf737a542fa7154e2aa` (September 25, 2026). Its skill-file SHA-256 is `87d28cd22e3a11340a15ab47fd17ea9060921d1fbe840ba86e453eab77a06a6e`.

The applied guidance is story first, real screen evidence, restrained masked typography, one main transition at selected chapter changes, stable proof holds, independent portrait composition and verification of the encoded deliverable. The production remains at 30fps to match the established delivery, rather than adopting the reference's 60fps default. No reference-video pixels, soundtrack, voice, logos or UI are included.

## Implemented motion language

The authored settings live in [build_compositions.py](../../videos/snap-to-league/scripts/build_compositions.py); chapter colors and the footage insert live in [build_edit.py](../../videos/snap-to-league/scripts/build_edit.py).

| Element | Implemented behavior |
|---|---|
| Headline | The opening hook is visible immediately. Later title lines rise from 108% below an overflow mask in 0.48s, with a 55ms line stagger and `power3.out`; entry begins 0.10s after the scene boundary. Captions remain stationary. |
| Marker and picture frame | The violet underline draws in 0.50s. A 2px SVG outline draws around the real picture in 0.55s. These decorate the frame; they do not imitate a product control or change the captured UI. |
| Chapter wipe | An opaque violet field with a pale edge crosses selected chapter boundaries with a −7° slant and `power2.in/out`. Landscape uses six wipes, 0.34–0.60s long; portrait uses three, 0.34–0.52s long. The screens themselves do not tilt or simulate navigation. |
| Chapter color | Light background `#F6F6FA` uses dark text `#22263B`; dark background `#191C31` uses `#FAFAFA`. Landscape is dark from 55.90–76.00 and 104.00–110.00; portrait is dark from 17.62–36.50. Accent colors are `#8186F1`, `#595ECC` and `#A4A7FF`. These are editorial backgrounds, not recolored product screens. |
| CTA | The final URL settles after a short 12px/0.30s entrance; the button's violet fill expands over 0.30s. The single invitation remains `TRY SNAP TO LEAGUE` with `snap.easychamp.com`, alongside the existing-platform disclosure. |
| Supporting motion | The progress line advances linearly. The finite readout bars are decorative rhythm, not an audio waveform or a measurement of voice activity. |

Landscape wipe boundaries are 23.98, 41.69, 55.90, 76.00, 88.78 and 104.00 seconds. Portrait boundaries are 7.20, 17.62 and 30.15. This is a speech-led edit, not a claim that all cuts are synchronized to a measured musical beat grid.

## Recovered camera shot

At film 11.00–13.40, the landscape uses take 9062, source 04.15–06.55: a genuine camera push-in with background parallax while Anton holds the paper and phone. The source soundtrack is muted, and the existing narration continues. At 13.40 the original handwriting picture resumes; no speech or caption timing moves.

The native SDR conversion is BT.709. The insert retains the full 1920×1080 picture with contain framing, applies a tracked feathered blur only to the visible badge, and uses a conservative shadow/midtone curve. Source white balance remains intact; a tested color adjustment was rejected because it distorted skin shadows. The treatment does not invent imagery, modify a score, imply a new dataset or manufacture a reaction. Hashes and treatment settings are recorded in [asset-provenance.json](../../videos/snap-to-league/reports/asset-provenance.json). Raw originals and private frame audits remain outside the public repository.

## Verification boundary

The recovered 72-frame clip and rebuilt picture-base boundaries were inspected and decoded. Landscape remains 110 seconds; portrait remains 36.5 seconds with its own layout. This document records the implemented source revision, not completed v2 publication or final-encode approval. Final encoded-frame, caption, sound and release checks are recorded separately in [EDIT-REVIEW.md](EDIT-REVIEW.md) and [RELEASE.md](RELEASE.md).
