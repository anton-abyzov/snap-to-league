# Market, competitors and marketing

## Competitors

A web scan in September 2026 found no product that turns a photo of a bracket, whiteboard, scoresheet or group-chat screenshot into a live league or tournament site. These are search results, not proof; some vendors' feature pages were not opened.

| Product | What it does with images | How close |
|---|---|---|
| Calendara (usecalendara.com) | Photo of a schedule, whiteboard or WhatsApp screenshot to calendar events; no standings or brackets. $4.99/mo | Closest input, different output |
| PicCal (piccal.ai) | Schedule photo or PDF to calendar events | Partial |
| ChessScan, Chess Scanner, Reine | Handwritten chess scoresheet to a game record | Partial, one sport, one game |
| Scoreboard OCR | Camera reads a lit scoreboard for broadcast graphics | Partial |
| Score7, LeagueLobster, LeagueRepublic, Tournify | CSV or pasted-Excel import only | None |
| Challonge, start.gg, Toornament | No image or AI import found | None |
| TeamSnap, SportsEngine, LeagueApps, Spond, Heja, GameChanger | Schedule or Excel import; their AI is scheduling | None |

The real substitute is pasting a photo into ChatGPT or Gemini and getting a table back. That gives no hosted page and nothing that updates with the next photo. Avoid confusion with SnapBracket (snapbracket.com, a free bracket builder).

**Gaps nobody fills:** photo to a live site in one step; updating a tournament from later photos; group-chat screenshots as a source; team-sport scoresheet reading; handwritten whiteboard brackets; one multi-sport engine behind it.

## Competitor revenue and market size (September 2026)

Revenue marked "est." comes from third-party estimators (Latka, Owler, Kona, Growjo), not the companies.

| Company | Revenue or funding | Users | Pricing |
|---|---|---|---|
| GameChanger (DICK'S) | ~$150M revenue FY2025 (10-K) | 10M active | Freemium, fan subscriptions |
| SportsEngine (sold to PlayMetrics, May 2026) | ~$105M (est.) | 5M+ users, 500k+ orgs | Per-org SaaS plus payments |
| TeamSnap | $35.6M ARR in 2020 (Latka); $100-250M now (est.) | 25M users | Freemium, club plans |
| LeagueApps | ~$20M (est.), raised $35M | n/d | Per-org plus payments |
| Spond | ~$11M revenue 2024, +83% | 3M+ MAU | Free app, payments |
| Challonge (independent since 2023) | ~$6.1M (est.) | 6M users, ~100k tournaments a month | Freemium, Premier |
| Toornament | ~$10M (est.) | 50k organizers | Subscriptions |
| Battlefy | $5-25M (est.) | 350k organizations | Enterprise, white-label |
| Score7 | n/d | n/d | Free for 1 tournament; $9 / $18 / $27 a month |
| OTTO Sport AI | $16.5M seed, Jan 2026 | n/d | n/d |

Sources: DICK'S 10-K, Variety, Latka, Tracxn, Shifter, Challonge blog, Owler, Kona Equity, Score7 KB, PR Newswire.

**Market size.** Sports management software: $4.3B in 2025 growing 17% a year (Grand View Research; Fortune Business Insights puts it at $369M, a narrower definition). Youth sports software: $0.7-1.8B in 2025, 9% a year. Esports tournament tools: $0.3-0.45B, 14-15% a year. About 30M US adults play in organized rec leagues, 90M+ Americans play team sports (SFIA 2026), and FIFA counts about 265M footballers worldwide.

**Bottom-up (assumptions):** about 2.5M reachable organizers worldwide still run on paper, spreadsheets or chats; 20% able to pay = 500k; at a blended $15 a month that is a ~$90M ARR serviceable market. Capturing 0.5-2% in 3-5 years is $0.45-1.8M ARR from subscriptions alone.

**Takeaway.** The big platforms earn from payments and registration, not bracket subscriptions (Challonge makes ~$6M from 6M users). Snap to League should stay free and bring organizers into EasyChamp, where registration fees and payments carry the revenue.

## Where it lives

- https://snap.easychamp.com, on EasyChamp's own Cloudflare, is the permanent home from day one, so search traffic is never split across domains.
- "Import from photo" inside the EasyChamp console for signed-in organizers comes next, on the same engine.

## Search pages

One free-tool page per sport and format, each with a live sample and a "try it" button:

- photo to bracket · turn whiteboard into bracket · scan tournament bracket
- convert handwritten bracket to digital · league table from photo
- import schedule from screenshot · whatsapp football league table
- intramural bracket maker · bar league standings app
- scoresheet scanner basketball / volleyball / futsal
- smash bracket from photo · fifa tournament table from screenshot

Schema.org `WebApplication` markup is already on the home page.

## Short videos (Reels, Shorts, TikTok)

- Three seconds: a marker-scrawled whiteboard, then a live league link on a phone.
- A messy WhatsApp screenshot becomes a league table: "your group admin's new superpower".
- "Send us your ugliest scoresheet" challenge, snapped live.
- Bar night: the bartender snaps the darts board and the TV announces the new leader.
- Side-by-side timer: snapping versus typing a bracket into Challonge.

## Communities

City pickup-soccer Facebook groups, r/bootroom, r/Smashbros local organizers, r/Pickleball, r/darts, r/PE_teachers, local gaming Discords, start.gg organizer threads, and QR table tents in trivia, darts and pool bars.

## Money

- Free: photo import and a live league page (the sign-up funnel).
- Paid organizer plan: unlimited leagues and photo updates, own domain, voice announcer, sponsor slots on league pages.
- Registration and team fees through EasyChamp's Stripe setup, with a platform percentage.
- Venues and rec departments: one price for every league they run.

At about 4 cents a photo with two readers, AI cost does not move any price.
