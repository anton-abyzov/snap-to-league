# Snap to League — Devpost draft

**Status:** Prepared copy; not a submission receipt.

**Tagline:** Turn a photo of your results into a competition people can follow.

**Demo:** [snap.easychamp.com](https://snap.easychamp.com)

**Source:** [anton-abyzov/snap-to-league](https://github.com/anton-abyzov/snap-to-league)

**Video:** `PENDING_FINAL_JUDGE_VIDEO_URL` — maximum 120 seconds

**Team:** Anton Abyzov and Anna Abyzova

**Discord contact:** `anton.abyzov`

## Inspiration

A scoresheet already contains the names, games and results an organizer needs. We wanted to start with a photo of that sheet, then make review and correction clear before sharing the competition.

We filmed the demo at ShellHacks using paper results and a phone. EasyChamp, the platform behind game publishing, existed before the event.

## What it does

Snap to League extracts a draft from photos or screenshots, computes standings from match results and flags inconsistencies. Organizers review names and scores and compare additional photos with a draft or saved competition.

Supported game competitions publish through EasyChamp after sign-in. Knockout results produce brackets. Races, trivia and cup-stacking results become placement boards shared on Snap; these do not publish as EasyChamp stages.

The in-product **Read out** control uses ElevenLabs when configured, with browser speech as a fallback. Our recording contains a genuine on-demand standings readout. Automatic announcement of changed match results is implemented separately in the saved board.

## How we built it

FastAPI handles photo jobs and publishing. Pydantic validates structured extraction; application code reconciles names, computes standings and presents checks. Gemini can read images through Google's API. An optional second reader compares extractions; an import can finish even if that second read fails.

EasyChamp sign-in identifies the publishing organizer. A Cloudflare Worker routes the demo hostname through a tunnel to a development Mac, so availability depends on that host and connection.

## Challenges and lessons

Similar spellings must be reconciled without merging opponents or players from different teams. Brackets need advancement relationships, not just scores. Model-extracted standings need comparison with calculations from the games.

A reviewable draft with explicit uncertainty is more useful than presenting extraction as infallible. The demo shows a scoresheet, reviewed standings, a knockout bracket and a voice readout; it makes no universal accuracy or processing-time claim.

## Existing components and event contribution

Our submission adds Snap's photo-import, review, reconciliation and publishing integration. **EasyChamp identity, league import, competition sites and Matchday design tokens predate ShellHacks.** Frameworks are listed in `pyproject.toml`; model and speech providers are external services. Repository history begins September 26, 2026, at `b079e20`.

## Challenge narratives

| Candidate entry | Product evidence |
|---|---|
| Best Overall | Working photo-to-competition workflow |
| Microsoft | AI helps complete a concrete task without a chat window |
| MLH Best Use of Gemini API | Actual image extraction through Google's Gemini API |
| MLH Best Use of ElevenLabs | Speech inside the app, supported by the real readout and provider evidence |

GoDaddy Registry remains conditional: no qualifying domain registration is established by `snap.easychamp.com`. Other service prizes require demonstrated use; an optional adapter is insufficient.

## Next

Move beyond development-host deployment, broaden representative image evaluation and improve review. Placement-based publishing in EasyChamp remains future work; shareable podiums on Snap already exist.

## Before submitting

Replace pending links and team details; select only supported challenge entries. Label previously published demo pages in the video and present existing EasyChamp as a dependency. Confirm the final video is at most 120 seconds. [Evidence notes](campaign/EVIDENCE-AND-CLAIMS.md) retain the current browser-audio limitation and distinguish source behavior from recorded proof.

[Official requirements](https://shellhacks-2026.devpost.com/) · [Official rules](https://shellhacks-2026.devpost.com/rules) · [Complete challenge matrix](campaign/RULES-AND-CHALLENGES.md)
