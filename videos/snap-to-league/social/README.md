# Two distinct social edits

- Personal: **Why I built Snap to League**, 27.5 seconds. Anton's original recorded speech, founder problem/inspiration, real proof. Follow Anton for real AI builds; YouTube handle is labeled explicitly.
- EasyChamp: **Your next result starts with a photo**, 31 seconds. Product workflow, a separate stock synthetic narrator, review/publishing/comparison proof, EasyChamp CTA.

Both are 1080×1920 / 30fps with burned captions. The source compositions are separate, with distinct shots, narration and calls to action. They use the established v2 typography/motion system. They are rendered with HyperFrames/GSAP, not Adobe After Effects.

See [the scripts](../../../docs/campaign/SOCIAL-SCRIPTS.md), [brief](BRIEF.md), [storyboard](STORYBOARD.md), and [provenance](reports/source-provenance.json). Publication is handled separately. AI video routing uses Anton Abyzov: AI Power on YouTube, never the family channel.

## Reproduce from approved public media

The approved-media package contains finished editorial picture-and-sound streams, plus safe muted cutaways. It excludes raw phone originals, private archive paths, isolated licensed music, and credentials. The fetch helper verifies the archive and every flat member before restoring media. Source footage assembly and narration-generation helpers are optional production recipes; public rendering does not need those private inputs or an API key.

Restore from the hash-pinned `snap-to-league-social-2026-v1` release:

```sh
python3 fetch_release_media.py
PWDEBUG=0 PLAYWRIGHT_HTML_OPEN=never npx --yes hyperframes@0.8.79 check personal
PWDEBUG=0 PLAYWRIGHT_HTML_OPEN=never npx --yes hyperframes@0.8.79 check easychamp
PWDEBUG=0 PLAYWRIGHT_HTML_OPEN=never npx --yes hyperframes@0.8.79 render personal --fps 30 --quality delivery --output renders/personal-ai-builds-1080x1920.mp4
PWDEBUG=0 PLAYWRIGHT_HTML_OPEN=never npx --yes hyperframes@0.8.79 render easychamp --fps 30 --quality delivery --output renders/easychamp-photo-results-1080x1920.mp4
```

Use the parent's pinned npm dependencies and local font/runtime setup before rendering. Browser automation remains headless. Do not invoke Studio/preview for automated checks.

## Audio and privacy

The founder cut contains genuine event speech. The product cut uses ElevenLabs eleven_v3 with a separate stock voice, disclosed in the script and post metadata. Neither camera cutaway's unrelated venue sound is included. The camera move has a tracked badge blur and a conservative shadow grade after native HLG-to-BT709 conversion. 9061 uses only the close phone shot; the later pan across bystanders and TV screens is excluded.

“Deep Urban” by Eugenio Mininni / Mixkit is licensed for use in the finished edits under the Mixkit Stock Music Free License. The underlying track is not redistributed. The production mix uses a measured, dynamic spectral carve below speech, with fades at the final ends. Distribution finishing applies one static gain to each complete mix and an oversampled peak limiter: personal −14.62 LUFS / −1.75 dBTP; EasyChamp −14.51 LUFS / −1.88 dBTP. The approved editorial files carry the same finished audio.
