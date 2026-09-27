"""Generate independent landscape and portrait HyperFrames compositions."""
from pathlib import Path
import json,html
from build_edit import LAND,VERT,captions

P=Path(__file__).resolve().parents[1]

def build(name,seq,dur,w,h):
 captions(name,seq)
 portrait=name=='vertical'
 scenes=[];anim=[]
 for i,s in enumerate(seq):
  start,length,a,at,pic,style,title,sub=s
  dark=style in ('phone','end') or pic in ('group','bracket')
  color='#FAFAFA' if dark else '#22263B'
  klass='narrow' if style in ('wide','proof') else ''
  if style=='end':klass+=' finale'
  lines=''.join(f'<span>{html.escape(t)}</span>' for t in title.split('\n'))
  label='SHELLHACKS 2026' if i<4 else ('TRY IT YOURSELF' if style=='end' else 'SNAP TO LEAGUE')
  text=f'<div class="scene-body {klass}" style="color:{color}"><div class="eyebrow">{label}</div><h1 id="title-{i}">{lines}</h1><div class="marker"><svg viewBox="0 0 300 18"><path id="mark-{i}" d="M3 11 C70 3 163 12 292 6" fill="none" stroke="#8186F1" stroke-width="11" stroke-linecap="round"/></svg></div><p class="sub">{html.escape(sub)}</p>'
  if pic in ('import','review'):
   text+='<div class="steps"><b>PHOTO</b><span>→</span><b>AI CHECK</b><span>→</span><b>YOUR REVIEW</b></div>'
  if style=='end':
   text+='<div class="cta">TRY SNAP TO LEAGUE <span>↗</span></div><p class="provenance">Built at ShellHacks on the existing EasyChamp platform.</p>'
  if pic=='update' and not portrait:
   text+='<p class="provenance">Built at ShellHacks: photo import + review. Pre-existing: EasyChamp publishing platform.</p>'
  if i==11 and not portrait:
   text+='<div class="voice-bars" aria-hidden="true">'+''.join(f'<i style="height:{v}px"></i>' for v in [24,48,82,58,112,80,42,64,92,48,28])+'</div>'
  text+='</div>'
  scenes.append(f'<section id="scene-{i}" class="clip scene" data-start="{start}" data-duration="{length}" data-track-index="2">{text}</section>')
  # One clear entry; long holds keep proof readable. First frame retains the hook.
  if i>0:
   anim.append(f'tl.fromTo("#title-{i} span",{{y:30,opacity:0,rotation:1.2}},{{y:0,opacity:1,rotation:0,duration:.5,stagger:.065,ease:"back.out(1.25)",immediateRender:false}},{start});')
  anim.append(f'tl.fromTo("#mark-{i}",{{strokeDasharray:310,strokeDashoffset:310}},{{strokeDashoffset:0,duration:.5,ease:"power2.out",immediateRender:false}},{start+.15});')
 caps=json.loads((P/'editorial'/f'{name}-captions.json').read_text())
 chtml=[]
 for i,c in enumerate(caps):
  chtml.append(f'<div id="caption-{i}" class="clip cap-track" data-start="{c["start"]}" data-duration="{c["end"]-c["start"]:.3f}" data-track-index="3"><div class="caption">{html.escape(c["text"])}</div></div>')
 css='''
 @font-face{font-family:Archivo;src:url(assets/fonts/archivo-400.ttf)}
 @font-face{font-family:Archivo;src:url(assets/fonts/archivo-700.ttf);font-weight:700}
 @font-face{font-family:ArchivoBlack;src:url(assets/fonts/archivo-black-400.ttf);font-weight:900}
 *{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden;background:#F6F6FA}
 #root{width:100%;height:100%;font-family:Archivo,sans-serif;position:relative;overflow:hidden}
 .clip{position:absolute;inset:0}.base{width:100%;height:100%;object-fit:cover}
 .scene{pointer-events:none}.scene-body{position:absolute;left:86px;top:180px;width:550px}
 .eyebrow{font-size:23px;font-weight:700;letter-spacing:3.4px;margin-bottom:42px}
 h1{font-family:ArchivoBlack,sans-serif;font-weight:900;font-size:76px;line-height:1.04;letter-spacing:-3px;width:100%;text-wrap:balance}
 h1 span{display:block}.marker{width:260px;height:22px;margin:29px 0 30px}.marker svg{width:100%;height:100%}
 .sub{font-size:28px;line-height:1.38;max-width:530px;font-weight:400}
 .narrow{width:425px} .narrow h1{font-size:66px;letter-spacing:-2px}.narrow .sub{font-size:26px}
 .steps{display:flex;gap:13px;align-items:center;margin-top:35px;font-size:15px;letter-spacing:1px;white-space:nowrap}
 .steps b{border:1px solid #8186F1;padding:10px 9px;border-radius:5px}
 .provenance{font-size:20px;line-height:1.4;margin-top:38px;max-width:570px}
 .finale{width:890px;top:174px}.finale h1{font-size:97px;letter-spacing:-3px}.finale .sub{font-size:48px;font-weight:700;letter-spacing:-1px;max-width:900px}
 .cta{display:inline-flex;gap:28px;align-items:center;background:#8186F1;color:#151729;padding:20px 26px;margin-top:32px;font-size:23px;font-weight:700;border-radius:10px}.cta span{font-size:30px}
 .cap-track{inset:auto 72px 84px;height:95px;display:flex;align-items:center;justify-content:center;z-index:5}
 .caption{font-size:43px;line-height:1.16;color:#fff;background:#151729;padding:13px 27px;border-radius:12px;font-weight:700;text-align:center;max-width:1650px;box-shadow:0 4px 24px #0002}
 .brand{position:absolute;left:86px;top:55px;height:48px;display:flex;align-items:center;font-weight:700;font-size:26px;letter-spacing:.3px;color:#FAFAFA;background:#595ECC;border-radius:6px;padding:11px 17px;z-index:8}
 .brand em{font-style:normal;opacity:.75;margin-right:13px;border-right:1px solid #FAFAFA66;padding-right:13px;font-size:20px}
 .folio{position:absolute;right:87px;bottom:32px;font-size:16px;letter-spacing:2px;color:#FAFAFA;background:#343950;padding:6px 10px;border-radius:4px;z-index:8}
 .voice-bars{height:120px;display:flex;align-items:center;gap:12px;margin-top:28px}.voice-bars i{display:block;width:12px;background:#8186F1;border-radius:8px}
 .progress{position:absolute;bottom:0;left:0;height:6px;width:100%;background:#8186F1;transform-origin:left center;z-index:9}
 '''
 if portrait:css+='''
 .scene-body{left:62px;top:198px;width:954px}.eyebrow{font-size:26px;margin-bottom:26px}
 h1{font-size:85px;line-height:1.04;letter-spacing:-3px}.marker{width:220px;height:15px;margin:22px 0 20px}
 .sub{font-size:29px;max-width:940px}.narrow{width:954px}.narrow h1{font-size:83px;letter-spacing:-3px}.narrow .sub{font-size:29px}
 .steps{display:none}.brand{top:95px;left:62px;font-size:27px}.brand em{font-size:21px}
 .cap-track{left:64px;right:64px;bottom:205px;height:150px}.caption{font-size:52px;max-width:950px;padding:17px 25px;line-height:1.15}
 .folio{right:64px;bottom:155px;font-size:19px}.finale{top:218px;width:960px}.finale h1{font-size:91px;letter-spacing:-3px}.finale .sub{font-size:53px;max-width:950px}.finale .marker{margin-top:25px}
 .cta{font-size:27px;margin-top:28px}.provenance{font-size:26px;max-width:880px;line-height:1.35;margin-top:760px}.voice-bars{display:none}
 '''
 doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width={w},height={h}"><title>Snap to League · {name}</title><script src="assets/vendor/gsap.min.js"></script><style>{css}</style></head><body>
 <div id="root" data-composition-id="{name}" data-start="0" data-duration="{dur}" data-width="{w}" data-height="{h}" data-fps="30">
 <video id="{name}-picture" class="clip base" data-start="0" data-duration="{dur}" data-track-index="0" src="assets/footage/{name}-base.mp4" muted playsinline></video>
 <audio id="{name}-final-mix" data-start="0" data-duration="{dur}" data-track-index="1" src="assets/audio/{name}-final.wav"></audio>
 {''.join(scenes)}{''.join(chtml)}
 <div class="brand"><em>EASYCHAMP</em> SNAP TO LEAGUE</div><div class="folio">SHELLHACKS / 2026</div><div id="progress" class="progress"></div>
 </div><script>const tl=gsap.timeline({{paused:true}});{''.join(anim)}
 tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{dur},ease:"none"}},0);
 window.__timelines=window.__timelines||{{}};window.__timelines["{name}"]=tl;</script></body></html>'''
 out=P if name=='landscape' else P/'portrait'
 out.mkdir(exist_ok=True)
 if portrait:
  if not (out/'assets').exists():(out/'assets').symlink_to('../assets',target_is_directory=True)
  (out/'hyperframes.json').write_text(json.dumps({'media':{'autoProxy':True}}))
 (out/'index.html').write_text(doc)

if __name__=='__main__':
 build('landscape',LAND,110,1920,1080)
 build('vertical',VERT,36.5,1080,1920)
