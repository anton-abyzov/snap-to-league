# Independent script and claims review — September 27, 2026

Reviewed `videos/snap-to-league/SCRIPT.md` v1 and six real-footage Scribe transcripts. Editorial review, not a substitute for verifying deployed product behavior. No source code changed. **Decision: strong concept; conditional approval after three claim/evidence fixes (L06, L07, L08), identity/eligibility confirmation and footage-level timing verification.**

## High-priority fixes

1. **L06 publishing proof:** an already-published league is proof of its displayed result, not proof the preceding upload created it. Keep “Already-published demo” visible throughout that scene, avoid a fake button-click match cut, and do not visually imply continuous upload→publish success. Preferred line if no fresh publication receipt: “Here is a published demo on EasyChamp, with matches, standings, and a shareable link.”
2. **L07 update proof:** requires an actual second-photo comparison, reviewed changes, same competition identity, and saved readback. If footage/receipt unavailable, replace spoken claim and scene with a genuine bracket proof beat. Do not ship promised update based only on screenshot of another task still working on it.
3. **L08 automatic-announcement implication:** “reads new results” plus “shared board” can suggest automatic live monitoring. Existing 9049 audio proves an on-demand standings readout; alone it does not prove automatic new-result announcements. Safer: “Tap Read aloud to hear the standings through ElevenLabs.” Follow with real captured announcement and verify provider attribution in source/runtime. Keep original app audio; do not regenerate announcement as if recorded live.
4. **At-event/pre-existing-work eligibility:** Devpost strictly forbids work outside hacking period and says presented work must have been created at event. Existing EasyChamp cannot become eligible merely through a disclaimer. Root must verify new layer's baseline/history and user/team's approved college-student eligibility, then resolve any uncertainty with organizers. No award promise.

## Line-by-line review

| Line | Verdict | Change / gate |
|---|---|---|
| L01 | Good hook; 10 words in 6s, readable | Show literal paper immediately and phone result by ~3s. Prefer caption “PAPER → LEAGUE”; “LIVE” may imply real-time refresh before proof. IMG_9062 transcript is unrelated venue speech, so mute it if used for visuals. |
| L02 | Clear benefit; conditional | “Competition people can follow” depends on visible shared/public result. Could tighten to “Snap to League turns a photo of your results into a league.” Keep actual format accurate if showing bracket. |
| L03 | Useful but overlaps L02 | Limit to inputs shown: photo of scoresheet/bracket + screenshot. Do not imply arbitrary unreadable handwritten text or every software export works. 11s is plenty; one concrete supported input can replace long list. |
| L04 | Strong technology beat, Gemini/Microsoft relevance | Verify deployed second-read behavior; “A second AI pass checks the extraction” is more precise than suggesting two independent providers. For standings, show points or match calculation; no accuracy guarantee. |
| L05 | Strong human-control beat | Real review/edit must be visible. “Correct anything uncertain” sounds like every field editable; “Review teams and scores. Fix a mistake before publishing” is narrower and clearer. |
| L06 | **Hold: proof mismatch** | Existing public result requires explicit label and revised line above if no fresh captured publish success. “League you own” requires ownership/permission evidence. |
| L07 | **Hold: missing update capture** | Show same competition ID before/after plus actual reviewed change. Otherwise replace with 9056 bracket sentence and real bracket. |
| L08 | **Hold: overstates observed trigger** | Use on-demand wording unless automatic change listener verified. Full original readout is 10.22s; narration + full readout cannot comfortably fit 11s. Use 66.96–70.68s sample (standings + first-place) then hold result, or give this beat 14–16s. |
| L09 | Risk of format/publish confusion | Say “Leagues and brackets publish to EasyChamp. Podiums share on Snap.” only if both publish paths verified. Otherwise brief visuals + explicit podium limitation. Avoid broad “format follows results” if auto-format selection fails on unsupported inputs. |
| L10 | Necessary provenance; legal eligibility still unresolved | Keep disclosure but verify exact event-period and location claim. Suggested factual line: “Our ShellHacks project adds photo import and review. EasyChamp was our existing platform.” Do not hide this only in tiny text. |
| L11 | Good brand payoff and CTA | Make URL readable ≥3s; do not speak full URL on noisy location audio if mispronounced. “Let the photo do the paperwork” is figurative, not a measurable savings claim. |
| V01 | Strong; 10 words/4s = 150 wpm | Visible physical problem before title motion finishes. Caption can hook while genuine Anton line begins. |
| V02 | Clear, demonstrable | Show actual upload+read, not purely montage. |
| V03 | Same L06 gate | If no real publish capture, use “Check the scores. Share the board.” only if board-share proof exists. |
| V04 | Same L07 gate | Replace with “A knockout bracket? That works too.” paired with 9056 genuine proof if update missing. |
| V05 | Good close | Nine-second window generous. Keep final CTA for 3s, music release without overpowering speaker. |

## Word budget and pacing

Current landscape copy: approximately 165 spoken words; vertical approximately 45. At 135–150 wpm, landscape voice fits in ~66–73s; add 12–20s genuine source speech/readout, 15–20s stable proof and transitions and deliver ~105–115s. Actual encode must remain ≤120s; target 112s leaves margin. The problem is L08's local timing, not total word count.

34s vertical easily fits 45 words, but long exposition would waste footage. Target 36–38s with one simple conversion and one outcome. Two-to-three-second stable proof holds after motion, not continual zooming while reading numbers. One CTA only.

## Genuine Anton soundbites: precise candidate cuts

Scribe timestamps are guidance; listen around boundaries and allow 100–200ms handles. Captions must follow actual final audio, not silently correct a wrong spoken model/domain.

| File and time | Use | Review |
|---|---|---|
| IMG_9043 0.88–3.08 | World Cup Miami setup | Genuine short contextual line; official FIFA sources confirm Miami hosted 2026 matches. Follow immediately with paper problem; do not include “Everybody,” “Millions,” or “most.” |
| IMG_9045 30.22–33.10 | Paper-results pain | Genuine phrase about paper tracking; starts with conjunction and pronoun, so retain clear preceding context or use under paper close-up as excerpt. No unsupported population statistic. |
| IMG_9049 11.80–15.42 | Library/live capture choice | Genuine useful instruction; leave out preceding misrecognized/mispronounced domain unless audio confirms correct snap.easychamp.com. |
| IMG_9049 57.30–65.00 | Recognized group-stage and readout introduction | Check screen actually displays scorers if retaining that word. Otherwise use first group-stage clause and cut before unsupported list. |
| IMG_9049 66.96–70.68 | Actual in-app audio sample | First result is 3.72s; enough proof within tighter beat. Full 66.96–77.18 readout is 10.22s. |
| IMG_9056 17.26–21.94 | Bracket result payoff | Strong genuine sentence listing games/bracket/winner. Preserve screen evidence. |
| IMG_9060 1.70–16+ | Source flexibility | Broad “any software/whatever” should not become quantified universal compatibility; trim to supported paper/screenshot/spreadsheet picture examples only. |
| IMG_9062 | Do not use speech | Transcript describes unrelated venue/business. No evidence these words explain product. |

**Cut problematic original claims:** 9049 ~29.4–33.9 contains “Gemini three point eight”; validate source audio, but prefer remove model number. 9056 ~25.6–31.8 promises storage “for the whole lifetime”; remove. 9049 ~79–93 implies indefinite access/reuse; replace with bounded demonstrated save/share. 9043/9045 contain unsourced “everybody,” “millions,” “most”; remove. “In the blink of an eye” (~26–29s) should not disguise actual processing duration. Edited elapsed time should be labeled if relevant.

## Best structure from actual footage

For judging: open on paper + phone result; genuine World Cup Miami line supplies local context; demonstrate image import; show human review and exactly one error/change; display result; play real ElevenLabs snippet; one bracket proof; disclose pre-existing platform; single CTA. Optional trivia podium stays a five-second breadth beat only if it does not displace core proof.

For vertical: caption hook over genuine paper; one photo→review→standings conversion; real speaker/result snippet; CTA. Do not spend half the reel listing formats or sponsor names. Gemini/ElevenLabs attribution can be concise overlay while proof runs. Microsoft challenge gets demonstrated by direct task completion, not logo collecting.

## Sources

- [ShellHacks requirements](https://shellhacks-2026.devpost.com/): submitted video 1–2min max; live guide 3min demo.
- [ShellHacks rules](https://shellhacks-2026.devpost.com/rules): event-created work and external-code disclosure.
- [FIFA Miami event report](https://ipt.fifa.com/organisation/news/miami-stadium-world-cup-2026-messi-england-france-6-4): verifies local World Cup context only; no footage-rights grant implied.
- Local Scribe evidence: `/tmp/shellhacks-contact-20260927/*-scribe-v2.json`; source recordings must be listened to before final cut.
