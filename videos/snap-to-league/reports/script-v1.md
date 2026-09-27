# Snap to League — script v1, before production

Status: editorial draft pending exact soundbite selection and independent claim-by-claim review. Target 108 seconds; absolute maximum 120 seconds for Devpost. Spoken copy below is English. Captions must match delivered speech.

## Creative selection

| Concept | Hook | Proof strength | Decision |
|---|---|---|---|
| Paper in one hand, phone in the other | “Your tournament is already here. Why type it all again?” | Real filmed presenter, paper, scan and results at ShellHacks | Main story; immediate physical before/after |
| Give the judge the marker | Viewer changes a score, resulting table updates | Strong live interaction; no recorded judge interaction yet | Live 3-minute demo playbook; do not fake reaction in film |
| One typo, two AI readers | “What happens when the score is wrong?” | Real warning and review UI | Middle proof beat; too abstract for opening |
| From football to gaming | Old football action + event gaming montage | Relevant context, but may imply historical product use | One optional clearly labeled context beat only; prefer current-event material |
| AI creates a cinematic stadium | Generated camera flythrough | Attractive, weak proof, dilutes demo | Reject for main film; generation limited to optional cover art |

## Landscape cut — target 108 seconds

| ID / target | Spoken line | Picture and edit | Claim / verification |
|---|---|---|---|
| L01 / 0–6 | “Your tournament is already here. Why type it all again?” | Real paper in Anton’s hand; match cut to phone. Oversized `PAPER → LIVE`, then settle. | Question, no numeric promise. IMG_9062 and IMG_9051. |
| L02 / 6–13 | “Snap to League turns a photo of the results into a competition people can follow.” | Hand writing scores, phone camera over same page. | Actual input and result recordings; do not claim footage is continuous across cuts. |
| L03 / 13–24 | “Photograph a whiteboard, a scoresheet, or a bracket. You can also import a screenshot from another app.” | One unambiguous photo upload on live app, then brief bracket source. Small `Demo data` for sample source. | Supported inputs in app/main.py; real footage and UI. |
| L04 / 24–36 | “Gemini reads the image. A second AI reader checks it. The app recalculates standings and flags results that need a human check.” | Real processing → warning → review. Labels trace each stage without fabricated response text. | Google Gemini API runtime; dual read; deterministic standings. Never say infallible. |
| L05 / 36–47 | “Check the teams and scores. Correct anything uncertain before publishing.” | Stable review hold; point to editable fields and warning. | Real editable form; manual review matters. |
| L06 / 47–60 | “Sign in to publish a league you own on EasyChamp, with standings, matches, and a link to share.” | Actual public existing demo league and its matches. Sign-in shown only if captured safely, never user credentials. | Existing EasyChamp dependency disclosed. Publishing demonstration must be real; screen label if showing an already-published demo. |
| L07 / 60–72 | “When the next result comes in, add another photo. Review what changed and update the same competition.” | Actual re-upload/change-review evidence. Hold changed score. | Verify current behavior; never fabricate click/change. |
| L08 / 72–83 | “And on a shared board, the ElevenLabs announcer reads new results out loud.” | Actual board and audible in-product voice. Narration stops for sample result announcement. | Must capture actual /api/speak response plus board invocation. Promotional TTS alone does not qualify. |
| L09 / 83–92 | “Football, a gaming bracket, even a trivia podium. The format follows the results.” | Quick real board sequence; `Podiums share on Snap` visible on trivia beat. | Podiums do not publish to EasyChamp; keep scope explicit. |
| L10 / 92–102 | “We built the photo import and review experience at ShellHacks, using the existing EasyChamp platform for league publishing.” | Brief 3-part architecture, then real event presenter. No claim existing platform was built this weekend. | Git history and dependency attribution; wording subject to eligibility confirmation. |
| L11 / 102–108 | “Keep playing. Let the photo do the paperwork. Try Snap to League.” | Paper and phone payoff, then clean `snap.easychamp.com` CTA. | Invitation; link must be HTTP200 and app usable. |

## Vertical cut — target 34 seconds, independently laid out

V01 (0–4): “Your tournament is already here. Why type it twice?” Real paper fill and energetic marker-box title.
V02 (4–11): “Take a photo. Gemini reads the results.” Real phone interaction, then legible app screen. `Demo data` where applicable.
V03 (11–18): “Check the scores. Publish a league people can follow.” Real review, then existing published demo labeled accordingly.
V04 (18–25): “Next game? Another photo. Same competition.” Actual update proof only.
V05 (25–34): “Keep playing. Let the photo do the paperwork. Snap to League.” Real presenter with paper and phone; CTA holds at least three seconds.

## Voice and sound

Prefer a clean, genuine Anton soundbite for opening or close if the recorded words fit. Use clearly synthetic narration only for connective lines; do not clone or impersonate another voice. Instrumental rhythmic bed, no lyrics, no sports-broadcast audio. Music gives way to speech and the actual announcer example. Final mixed loudness target -14 LUFS, true peak ≤ -1.5 dBTP.

## Motion and source rules

Use Anton’s motion-graphics-promo v1.1.0: one energetic entry; one main transition per task; 2–3 seconds of stable proof after motion. Real UI remains unmodified. Generated art is optional packaging only. Tone-map iPhone HLG to Rec.709 before grading; preserve source originals. Archive older event recordings separately, never imply they are current ShellHacks activity or product testimonials.

## Review gates

Every line checked for factual support, challenge relevance, natural speech, frame readability and timing. Reject unverifiable superlatives, accuracy generalizations, adoption claims, false continuity, and invented reactions. No winner claims. Independent review required before source publication and final render.
