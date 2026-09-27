# Devpost submission

**Name:** Snap to League

**Tagline:** Photo of the board. Live league in seconds.

**Links:** https://snap.easychamp.com · https://github.com/anton-abyzov/snap-to-league

**Tracks to tick:** Best Overall · Microsoft "What's Missing?" · MLH Best Use of Gemini API · MLH Best Use of ElevenLabs · MLH Best Domain Name from GoDaddy Registry

## Inspiration

Every weekend thousands of tournaments run on a whiteboard, a paper scoresheet or a group chat. League apps want you to type every team and score back in, so organizers never do, and players never get a table. We wanted the organizer's only job to be taking a photo.

## What it does

Snap one or more photos of a whiteboard, scoresheet or bracket, or screenshots from Challonge, start.gg or a league website. Two AI readers read every result; the app recomputes the table, flags anything doubtful with a yellow card, merges pages and spelling variants, attaches scorers, and shows exactly what a new photo changed. One tap publishes a real league on EasyChamp with standings or a bracket, rosters and goal events. A board left on a TV announces every new result out loud.

## How we built it

- FastAPI back end; plain HTML and ES modules on EasyChamp's Matchday design tokens.
- Gemini 3.8 Flash through the Gemini API reads each photo; GPT-6 Astra reads it in parallel as a second opinion. Organizers can choose open-weight readers (GLM 5.3 Flash, Qwen 3.8 Flash).
- Pydantic validation, our own standings engine and merge rules; we never trust the model's table.
- EasyChamp's league import creates the league site, knockout rounds, rosters and scorer events.
- ElevenLabs voices the announcer.
- A Cloudflare Worker serves snap.easychamp.com in front of a Cloudflare Tunnel.

## Challenges

- The first vision model we tried for player tracking in match video refused person re-identification, so we moved AI to what it does best: reading handwriting and screens.
- Brackets: EasyChamp draws a bracket from round names and positions, so we rebuild the tree from who advanced.
- Keeping a public app safe: a publish PIN, per-device limits, a daily AI budget, and keys that never leave the server.

## Accomplishments

- 37 of 39 results read correctly from real Challonge, start.gg and Score7 screenshots; 30 of 30 standings rows from start.gg and LeagueRepublic.
- Two scoresheets taken a week apart merge into one league with 15 goals by 8 scorers in 8 seconds.
- A photo becomes a real EasyChamp league site with the right quarterfinal, semifinal and final.

## What we learned

A cheap fast model with a second opinion beats one expensive model: Gemini 3.8 Flash read our samples perfectly at about half a cent a photo, and disagreements between readers are the best signal for what a human should check.

## What's next

"Import from photo" inside the EasyChamp console, per-sport search pages, and races, quizzes and judged contests as new competition formats.
