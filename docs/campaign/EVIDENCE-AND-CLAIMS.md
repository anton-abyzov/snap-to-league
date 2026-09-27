# Evidence and claim boundaries

Reviewed September 27, 2026. This record distinguishes an implemented feature, a recorded demonstration and a fresh deployment check. None is interchangeable with the others.

| Claim | Current support | Public wording |
|---|---|---|
| Photo import, review and standings | Source implementation and current-event phone recordings | “Import a photo, review teams and scores, then view standings.” |
| Two-reader comparison | Configured implementation plus completed fresh-import receipts; second reader can fail independently | “A second pass checks the extraction” is supported for the captured fresh imports. Avoid universal guarantees; cached images and failed/disabled secondary reads differ. |
| Gemini API | Direct Google API path when the Gemini credential is configured; other provider paths also exist | Name Gemini for a run only when its actual reader/provider is verified. Avoid unverified model-version or accuracy claims. |
| Signed-in publishing | `app/auth.py` and publish handlers validate identity and use the user's token | “Sign in with EasyChamp to publish supported game competitions.” Legacy operator PIN is a separate path. |
| Published league result | Existing demo pages and retained screenshots | Label pre-existing published results. A page does not prove a preceding edited click created it. |
| Update same competition | Fresh photo comparison captured against an unsaved draft; no new EasyChamp publication during capture | “Add another photo and review what changed.” A saved/published update requires separate evidence. |
| Podiums | Ranking and shared-board implementation | “Podiums share on Snap.” Do not claim EasyChamp placement-stage publishing. |
| Read out | Real phone recording IMG_9049 contains audible in-product standings; short direct speech-endpoint check returned valid audio | “The recorded demo includes an on-demand standings readout.” |
| Automatic announcer | Saved-board code polls and can speak changed matches | Implemented, but not proved by an on-demand readout. No cross-browser reliability promise. |
| Latest browser audio check | Automated browser readout response was empty even though the short endpoint test succeeded | Do not mark the browser voice flow fully verified or synthesize a replacement and present it as live app audio. |
| Public availability | Worker plus quick tunnel to a development Mac; address was repaired during preparation | “Public hackathon demo.” Availability depends on host/tunnel. |
| Accuracy, speed, cost, test totals | Historical tables and scripts exist; no fresh campaign-wide measurement established here | No numerical performance promise or fixed test count. |
| GoDaddy Registry entry | Official offer exists; no qualifying registered domain verified | Not an entered/qualified challenge yet. |

## Release evidence to retain

Bind each published video to its source commit, final-file hash, dimensions, duration, captions and music/voice provenance. Record screenshots or API receipts separately from public post URLs. A scheduled post is not a published post; a provider receipt is not proof that the public page plays correctly.

Use the recorded founder's exact speech. Cut unsupported population estimates, incorrect model/domain pronunciation and lifetime-storage promises. Clearly label sample data and event-context footage. Cup-stacking activity footage supplies context; it is not a testimonial or evidence of adoption.

## Provenance and review

The event contribution is Snap's photo-import/review experience and integration. EasyChamp and its existing services are dependencies, not event-built functionality. [ShellHacks rules](https://shellhacks-2026.devpost.com/rules) require event-created work and disclosure of external code. The user's participant eligibility has been confirmed; this does not substitute for accurately describing project provenance.
