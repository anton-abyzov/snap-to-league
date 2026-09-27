# ShellHacks 2026 — verified rules and challenge fit

Checked September 27, 2026, against the official guide and event Devpost. Challenge fit below is a project assessment, not confirmation of an entry or award.

## Urgent constraints

- **Deadline: Sunday September 27, 2026, 11:00 am EDT.** Both hacking and submission stop then. Devpost explicitly says EDT; guide's EST label is inconsistent. Use 11 am Miami local time, not noon.
- **Submitted video: 1–2 minutes maximum.** Make the judge master ≤120 seconds. Separate social cuts can differ.
- **Live presentation: in person, 3 minutes.** If selected for round 2: 3–5 minutes. Follow Discord table/room assignments and be at designated spot by 1 pm; noncompliance can disqualify.
- **Eligibility:** Devpost lists college students only, above legal majority in country of residence, all countries except standard exclusions. Anton confirmed registered eligibility on September 27; no additional identity evidence is published here.
- **Pre-existing work:** official rules prohibit projects including work done outside the hacking period; what is presented must have been created at the event. Libraries, frameworks and open-source code are allowed only with explicit attribution in submission and oral judging. Existing EasyChamp must be identified as pre-existing infrastructure. A new Snap to League layer integrating with it needs clear event-period provenance; attribution alone does not prove the integration is eligible. Organizer clarification is required if substantial pre-existing proprietary functionality forms the submission.
- No submission of this project to other hackathons. One project per team; at most four hackers.

Primary sources: [Devpost overview](https://shellhacks-2026.devpost.com/), [Devpost rules](https://shellhacks-2026.devpost.com/rules), [official guide](https://shellhacks.net/guide) and its [public Notion content](https://conscious-caper-fec.notion.site/Hacker-Guide-2fb42bb969488004965ee136c468bc12), updated 09/26/2026.

## Submission checklist

- One Devpost project; creator invites every team member before submitting.
- Use same email as ShellHacks registration; first/last names, or identify full names in comments.
- Include at least one Discord tag so organizers can contact team.
- Attach GitHub repository link; keep judged source accessible. The inspected official pages require a GitHub link without explicitly specifying visibility; this project is being prepared as public source.
- Include ≤120-second demo video, concise problem/solution/implementation/impact, technologies, and clear proof of actual working features.
- Select sponsor prize categories before deadline; guide warns missing prize selection means no prize consideration even though it separately calls Best Overall automatic. Explicitly check every appropriate option including overall when available.
- Document reused frameworks, libraries, open-source code, pre-existing services and external media; distinguish event work and mention external-code attribution during judging.
- Record baseline commit, event-period commits, deployment SHA and public demo URL. Never claim pre-existing EasyChamp was created this weekend.
- Do not invent a public-video-host rule, mandated YouTube visibility, aspect ratio, branding requirement, or GitHub license requirement: none was stated on the inspected official pages. A public/unlisted accessible judge link is sensible delivery advice, not a discovered rule.

## All listed challenge categories and fit

Fit below is an assessment against current source and recorded evidence. No challenge entry or Devpost submission is established by this table.

| Category | Official qualifying subject | Snap to League fit / evidence |
|---|---|---|
| Best Overall (1st–3rd) | In-person project, creativity/execution/impact | Strong; demonstrate real capture → corrected structure → useful result. Automatic per overview, still inspect category selection. |
| Best First-Time Hacker | At least 50% of team submitting first hackathon project | Conditional on actual team history. |
| Microsoft | AI improves real task; core experience cannot be chatbot or depend on chat window | Strongest topical fit. Show handwritten board becoming usable league/bracket through direct UI, not chat. No Microsoft-specific service requirement stated. |
| MLH Best Use of Gemini API | Build functional AI app using Google Gemini API | Supported by fresh imports through Google’s API and completed extraction receipts. Name the actual provider truthfully; demonstrate review and result. |
| MLH Best Use of ElevenLabs | Integrate autonomous audio experience into hack | Viable candidate: the original phone recording has genuine in-product readout and direct endpoint tests returned audio. Automatic changed-result announcement exists in source but was not proved end to end in the fresh browser capture. Demonstrate that behavior for the autonomous-audio wording; promo narration alone is insufficient. |
| MLH Best Domain Name from GoDaddy Registry | Register domain via GoDaddy Registry offer | Conditional new qualifying domain and working project linkage; current snap.easychamp.com subdomain alone does not establish qualification. |
| MLH Best Use of MongoDB Atlas | Actual MongoDB Atlas use | Not demonstrated: an optional MongoDB adapter and local storage do not establish Atlas. Requires a real Atlas data path. |
| MLH Best Use of DigitalOcean | Actual cloud infrastructure/service use | Not demonstrated: current deployment uses Cloudflare and a Mac. Requires genuine DigitalOcean service use. |
| MLH Best Use of Tiger Data | Innovative, impactful, performance-driven use of Tiger Data/Postgres capabilities | Unsupported absent actual implementation. |
| MLH Best Use of Snowflake API | Actual Snowflake APIs in app | Unsupported absent actual implementation. |
| MLH Best Use of Solana | Product built on Solana; fast/high-frequency transactions etc. | Unsupported absent actual implementation. |
| Assurant | Mindful AI: privacy, spending visibility or confident tool choice | Weak unless user-facing data control/review/deletion is substantive demonstrated feature. Do not claim privacy protection merely because UI has confirmation. |
| Waymo | Transportation improvement using public data | Not currently relevant; sports app by itself does not qualify. |
| Sperry Tech | Compare ≥2 utilities' public future construction plans; flag geographic/time overlap | Not relevant. |
| Blackstone | Help investors understand current investments/research opportunities using public finance/economic data | Not relevant. |
| State Farm | Make auto insurance simpler/help students reduce theft/fire/accident risk where living/studying/traveling | Not relevant. |
| INIT National | Help student builders collaborate over weeks/months, find teammates, share knowledge, mentorship, overcome blocks | Not established by league-management use; only enter if actual student-building collaboration workflow exists. |

Source: [event Devpost overview](https://shellhacks-2026.devpost.com/). Do not import 2025 categories: 2026 does **not** list the 2025 Google ADK/A2A challenge, Auth0, Wix/Base44, Netflix, GitHub or Wolfram prizes. Guide uses “MLH - Google Cloud” heading; Devpost names the current sponsor category “Best Use of Gemini API.” Event-specific list controls over generic MLH prize list.

## Domain decision

[Official MLH GoDaddy prize link](https://mlh.link/GoDaddyRegistry) resolves to [tech.study](https://www.tech.study/). Current landing page instructs: search domain, choose available name, complete registrant form with event organizer promo code. It features .US; other selectable eligible suffixes and redemption terms were not verified in this pass.

**Recommendation:** keep snap.easychamp.com canonical; if a short brand domain improves story and qualifies through actual organizer offer, point/redirect it to current platform and test HTTPS + path behavior. Do not buy a random .com through Cloudflare and claim that it qualifies for GoDaddy Registry. Registry and registrar differ; eligibility of a paid alternative requires organizer confirmation. Price and availability not checked; no ~$10 promise. No purchase or registration performed.

## Judging and demo strategy

Five criteria: completion, originality, design, technology and practicality. Devpost also describes overall judging as creativity, execution and impact. Best evidence sequence: real handwritten source → Gemini extraction → human correction/reconciliation → deterministic standings/bracket → public result. Show feature limitations honestly. For races/quizzes/cup stacking, do not claim publishing to EasyChamp unless actual supported flow is proven.

## Venue, conduct and promotional side rules

- Badge required for entry/workshops/meals/swag. Physical ID name must match registration; bring dashboard QR. Late arrivals should use organizer late-check-in form.
- No extension cables, large mattresses/tents, moving venue furniture, monopolizing rooms or disruptive noise; clean up. Room 272 unavailable; upper-floor rooms after 5 pm; sleeping rooms 278B/279A/280 are sleeping only.
- Follow [MLH Code of Conduct](https://github.com/MLH/mlh-policies/blob/main/code-of-conduct.md): respectful/inclusive behavior, no harassment, sexualized event/hack material or harassing recordings; stop behavior when asked. Applies at event, related social events, transportation and online interactions. Incident reporting: incidents@mlh.io; North America +1 409 202 6060.
- Optional Instagram social contest: public account all weekend, stories with #shellhacks + @init.fiu; winner announced closing ceremony and must be on campus to receive that prize. This is separate from submission eligibility.
- Registration raffle winner must be present. General project prize shipping language differs; do not extrapolate raffle presence rule to every prize.
- Event photos/video will be released afterward. Availability is not permission to reuse all footage commercially; retain consent/license checks.

## Evidence and limits

Research retained local read-only captures of the official guide, Devpost and domain offer. Public guide fetched before later Notion anti-bot challenge blocked further toggle expansion. Sponsor requirements read in full from current Devpost instead. No challenge bypass, account action, submission, purchase, or publication performed.
