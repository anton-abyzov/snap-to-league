# Second-reader claim audit — September 27, 2026

Approved bridge: **“A second AI pass checks the extraction.”** This accurately describes this deployed configuration and captured fresh imports. Avoid “every photo always gets two successful reads”, “both always agree”, or perfect-accuracy guarantees.

Live `/api/health` reported `checked:true`, primary `google/gemini-3.8-flash`, readers `gemini-3.8-flash + gpt-6-astra`, Google Gemini provider route and app version`cf109a0609` during capture.

Deployed app source: `app/jobs.py:56-62` chooses main/secondary models; `app/jobs.py:96-106` starts independent secondary reads; `app/jobs.py:130-151` compares completed extraction and writes disagreement cards. `app/extract.py:163` configures default second model; `app/extract.py:195-205` routes Gemini directly to Google when configured.

Persisted actual job receipts read after completion, not inferred from health alone:

| Capture | Job | Gemini first result | Astra check | Total until checked |
|---|---|---|---|---|
| Portrait before | cc751591baca |4matches,5.4s |finished;1difference |13.7s |
| Portrait update | c5c7059d2e54 |4matches,5.7s |finished;agrees |11.2s |
| Desktop before |32f19568140e |4matches,4.8s |finished;agrees |12.0s |
| Desktop update |f5b2e90c4e0a |4matches,2.7s |finished;1difference |12.6s |
| Built-in bracket |2502352e37c5 |7 matches, 7.0 s |finished; agrees |11.2 s |
| Replacement portrait before |3b67326d821c |4 matches, 5.3 s |finished; agrees |16.1 s |
| Replacement portrait update |95d26e9740e6 |4 matches, 4.5 s |finished; 1 difference |13.1 s |

The primary read appears before the secondary finishes. Some footage shows “Double-checking every result” while work continues. Completed receipts are in`product-proof-assets.json`; the actual prerecorded footage must not imply secondary completion at an earlier time.

Limitations: duplicate-image cache returns saved read without a new model check; secondary model failures are optional/degrade gracefully; alternate configuration can disable the second model. These make universal guarantees inaccurate. This capture proves the stated deployed feature, not all future sessions.
