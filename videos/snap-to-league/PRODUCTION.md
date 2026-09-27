# Snap to League — editable video package

Two independent compositions: `index.html` (1920×1080, 110s) and `portrait/index.html` (1080×1920, 36.5s). Both run at 30fps. The portrait is designed separately; it is not a crop of the landscape master.

The script was written before editing, independently checked against word-timed source transcripts, then corrected after frame inspection. [SCRIPT.md](SCRIPT.md) describes the final dialogue and disclosure boundaries. Machine-readable shot decisions and captions are in `editorial/`; subtitle sidecars are `landscape.srt` and `vertical.srt`.

## Re-render the approved cut

Requirements: Node, npm, Python 3, FFmpeg and GitHub CLI. Run from this directory:

```sh
npm ci
python3 scripts/fetch_release_media.py
npm run check
npm run check:portrait
npm run render
npm run render:portrait
```

The release media bundle contains the approved picture-and-sound edits as videos. The fetch script verifies their hashes and separates local render tracks. It does not download private camera originals, personal photo-library views, badge details or an isolated music track. Captions and titles remain editable HTML/GSAP source. Render files are written under `renders/`.

## Editorial source workflow

`scripts/prepare_sources.py` uses Apple's `avconvert` H.264 preset to convert iPhone HLG/BT.2020 material to verified BT.709 SDR. It requires `SNAP_MEDIA_ARCHIVE` to identify the owner's private archive. Source recordings remain unchanged. `scripts/build_edit.py` assembles one picture track per format, edits the original speech, adds two disclosed ElevenLabs bridges, ducks and spectrally carves the licensed instrumental, and generates captions. Set `SNAP_TRANSCRIPTS` to the private Scribe word-timing directory when rebuilding that editorial cut.

`scripts/build_compositions.py` generates the independent layouts. One seekable GSAP timeline controls type entrances, marker strokes and a progress line. All fonts and GSAP are local at render time. The video base is pre-concatenated to avoid the known multi-video overlay dropout; final encoded frames still require inspection.

Real app screenshots and recordings are factual evidence, not recreated interfaces. The live capture uses labeled demo data. The original recorded readout retains its matching Panthers / Organizers / Wizards / ShellHacks results. Separate EasyChamp outputs are labeled separately. The dark physical knockout shot was replaced by a legible, labeled live Snap sample; speech about an unshown winner was removed.

## Rights and delivery boundaries

Music: “Deep Urban,” Eugenio Mininni, [Mixkit Stock Music Free License](https://mixkit.co/license/modal/musicFree/). Integrated web/social video use; the raw track is not distributed. Archivo and Archivo Black carry their OFL notices. The two promotional bridge takes use ElevenLabs `eleven_v3`, a separate narrator voice, not a founder clone. Source and hashes are in [asset-provenance.json](reports/asset-provenance.json).

Public app/source availability is separate from Devpost submission and social posting. This package does not submit or schedule either. AI YouTube content is intended for **Anton Abyzov: AI Power (@antonabyzov)**. See the [campaign plan](../../docs/campaign/CAMPAIGN.md).

The public demo currently depends on an awake development Mac and a Cloudflare tunnel. Keep the verified recording available for judging. A new domain was not needed for this cut; the existing `snap.easychamp.com` remains the canonical URL.
