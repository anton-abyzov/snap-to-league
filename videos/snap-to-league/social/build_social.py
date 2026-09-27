"""Independent social edits. Raw originals stay private; source paths are resolved locally."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,html,hashlib,shutil,os
S=Path(__file__).resolve().parent; P=S.parent; A=S/'assets'; F=P/'assets/footage'; R=P/'assets/proof'
for p in [A/'footage',A/'audio',S/'reports',S/'renders',S/'.private']:p.mkdir(parents=True,exist_ok=True)

def run(args):
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-4500:])
 return r.stdout

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# Safe, real phone detail from the newly inspected 9061; no later bystander pan.
phone=A/'footage/9061-phone-safe.mp4'
if not phone.exists():
 run(['ffmpeg','-y','-v','error','-ss','0.1','-i','/tmp/shellhacks-9061-sdr.mov','-t','1.6','-vf',"crop=1080:1080:440:0,curves=master='0/0 0.04/0.065 0.10/0.18 0.25/0.40 0.50/0.63 0.75/0.83 0.92/0.95 1/1',fps=30,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",'-an','-c:v','libx264','-crf','17','-preset','fast','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',phone])

# shot: start,duration,source,source start,crop,box,dark,still. Proof plays at real-time speed.
# Full-frame 9062 preserves face and both props; privacy blur is baked in.
PERSONAL=[
 (0,2.7,A/'footage/9062-drift-safe-graded.mp4',0,None,(60,570,960,540),True,False),
 (2.7,5.6,F/'9051-sdr.mp4',0,(500,0,1080,1040),(60,520,960,960),False,False),
 (8.3,6.58,R/'portrait-clean-live-import-and-update-2x.mp4',8.1,(0,500,860,1150),(90,520,900,980),False,False),
 (14.88,3.79,F/'9049-sdr.mp4',57.16,(220,0,1080,1080),(60,520,960,960),False,False),
 (18.67,3.83,R/'04-review-phone.png',0,(0,100,860,1040),(90,530,900,960),False,True),
 (22.5,5,None,0,None,None,True,False),
]
PRODUCT=[
 (0,1.6,phone,0,None,(60,520,960,960),True,False),
 (1.6,1.9,F/'9051-sdr.mp4',0,(500,0,1080,1040),(60,520,960,960),True,False),
 (3.5,4.5,R/'portrait-clean-live-import-and-update-2x.mp4',8,(0,500,860,1150),(90,520,900,980),False,False),
 (8,3.6,R/'portrait-clean-live-import-and-update-2x.mp4',11.05,(0,500,860,1150),(90,520,900,980),False,False),
 (11.6,3.2,R/'11-group-desktop-v2.png',0,(168,130,1104,620),(60,630,960,540),True,True),
 (14.8,6.5,R/'10-update-comparison-phone.png',0,(0,0,860,1040),(90,520,900,980),False,True),
 (21.3,3.9,A/'footage/9062-drift-safe-graded.mp4',0,None,(60,570,960,540),True,False),
 (25.2,5.8,None,0,None,None,True,False),
]

def shot(job):
 name,i,s=job;t,d,src,ss,crop,box,dark,still=s;out=A/'footage'/f'{name}-{i:02}.mp4';bg='0x191C31' if dark else '0xF6F6FA';n=round((t+d)*30)-round(t*30);seconds=n/30
 if out.exists():return out
 args=['ffmpeg','-y','-v','error','-filter_complex_threads','2']
 if src is None:
  args+=['-f','lavfi','-i',f'color=c={bg}:s=1080x1920:r=30:d={seconds}'];filt=None
 else:
  args+=['-loop','1'] if still else ['-ss',str(ss)]
  args+=['-i',src,'-f','lavfi','-i',f'color=c={bg}:s=1080x1920:r=30:d={seconds}']
  chain=''
  if crop:
   x,y,w,h=crop;chain+=f'crop={w}:{h}:{x}:{y},'
  x,y,w,h=box
  chain+=f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg},setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds},setpts=PTS-STARTPTS'
  filt=f'[0:v]{chain}[s];[1:v][s]overlay={x}:{y}:shortest=1,format=yuv420p[v]'
 if filt:args+=['-filter_complex',filt,'-map','[v]']
 args+=['-an','-frames:v',str(n),'-c:v','libx264','-crf','17','-preset','fast','-threads','3','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',out]
 run(args);return out

# Separate speech edits and exact captions; product narration is a disclosed non-cloned voice.
TRANS=Path('/tmp/shellhacks-contact-20260927')
VOICES={
 'personal':[(0,2.7,F/'9043-sdr.mp4',5.8,'9043',5.8),(2.7,3.2,F/'9045-sdr.mp4',2.14,'9045',30.14),(5.9,8.98,F/'9045-sdr.mp4',7.52,'9045',35.52),(14.88,3.79,F/'9049-sdr.mp4',57.16,'9049',57.16)],
 'easychamp':[(.2,1.92,A/'audio/easychamp-narrator.mp3',0,'tts',0),(3.7,3.45,A/'audio/easychamp-narrator.mp3',2.11,'tts',2.11),(8.2,1.83,A/'audio/easychamp-narrator.mp3',5.61,'tts',5.61),(11.8,1.71,A/'audio/easychamp-narrator.mp3',7.49,'tts',7.49),(15,4,A/'audio/easychamp-narrator.mp3',9.28,'tts',9.28),(21.5,3.37,A/'audio/easychamp-narrator.mp3',13.35,'tts',13.35),(25.4,3.12,A/'audio/easychamp-narrator.mp3',16.88,'tts',16.88)]
}

def ttswords():
 d=json.loads((A/'audio/easychamp-narrator.json').read_text());a=d.get('normalized_alignment') or d['alignment'];out=[];word=''
 for c,b,e in zip(a['characters'],a['character_start_times_seconds'],a['character_end_times_seconds']):
  if c.isspace():
   if word:out.append(dict(text=word,start=st,end=end,type='word'));word=''
  else:
   if not word:st=b
   word+=c;end=e
 if word:out.append(dict(text=word,start=st,end=end,type='word'))
 return out

TW=ttswords()
def audio(name,duration):
 tracks=[];words=[]
 for i,(t,d,src,ss,tag,original) in enumerate(VOICES[name]):
  dst=A/'audio'/f'{name}-speech-{i}.wav';f=f'atrim=duration={d},asetpts=PTS-STARTPTS,highpass=f=85,lowpass=f=11000,'
  if tag!='tts':f+='afftdn=nf=-30:nr=7,'
  f+=f'loudnorm=I=-17:TP=-2:LRA=9,aresample=48000,afade=t=in:d=0.006,afade=t=out:st={max(0,d-.015)}:d=0.015'
  run(['ffmpeg','-y','-v','error','-ss',ss,'-i',src,'-t',d,'-af',f,'-ar','48000','-ac','2',dst]);tracks.append((dst,t))
  ws=TW if tag=='tts' else json.loads((TRANS/f'139APPLE_IMG_{tag}-scribe-v2.json').read_text())['words']
  for w in ws:
   if w['type']=='word' and w['start']>=original-.02 and w['end']<=original+d+.02:
    words.append(dict(text=w['text'],start=round(t+w['start']-original,3),end=round(t+w['end']-original,3)))
 args=['ffmpeg','-y','-v','error'];f=[]
 for path,t in tracks:args+=['-i',path]
 for i,(p,t) in enumerate(tracks):f.append(f'[{i}:a]adelay={round(t*1000)}|{round(t*1000)}[s{i}]')
 f.append(''.join(f'[s{i}]' for i in range(len(tracks)))+f'amix=inputs={len(tracks)}:normalize=0,apad,atrim=duration={duration}[v]')
 # Assemble finite PCM arrays: avoid amix/apad timestamp behavior on short fragments.
 import wave,numpy as np
 samples=np.zeros((round(duration*48000),2),dtype=np.float64)
 for path,t in tracks:
  with wave.open(str(path),'rb') as wf:
   assert wf.getnchannels()==2 and wf.getsampwidth()==2 and wf.getframerate()==48000
   pcm=np.frombuffer(wf.readframes(wf.getnframes()),dtype='<i2').reshape(-1,2)
  start=round(t*48000);length=min(len(pcm),len(samples)-start);samples[start:start+length]+=pcm[:length]
 with wave.open(str(A/'audio'/f'{name}-voice.wav'),'wb') as wf:
  wf.setparams((2,2,48000,0,'NONE','not compressed'));wf.writeframes(np.clip(samples,-32768,32767).astype('<i2').tobytes())
 # Separate full-duration bed for the HyperFrames dynamic spectral-carve pass.
 run(['ffmpeg','-y','-v','error','-ss','12' if name=='personal' else '39','-i',A/'audio/deep-urban.mp3','-t',duration,'-af',f'loudnorm=I=-23:TP=-4:LRA=8,afade=t=in:d=0.16,afade=t=out:st={duration-1.2}:d=1.2','-ar','48000','-ac','2',A/'audio'/f'{name}-music.wav'])
 caps=[];g=[]
 for w in words:
  if g and (len(g)>=5 or w['start']-g[-1]['end']>.55 or len(' '.join(x['text'] for x in g)+w['text'])>37):
   caps.append(dict(start=g[0]['start'],end=g[-1]['end']+.05,text=' '.join(x['text'] for x in g)));g=[]
  g.append(w)
  if w['text'].endswith(('.', '?', '!')):
   caps.append(dict(start=g[0]['start'],end=g[-1]['end']+.05,text=' '.join(x['text'] for x in g)));g=[]
 if g:caps.append(dict(start=g[0]['start'],end=g[-1]['end']+.05,text=' '.join(x['text'] for x in g)))
 for i in range(len(caps)-1):caps[i]['end']=min(caps[i]['end'],caps[i+1]['start'])
 (S/name/'captions.json').write_text(json.dumps(caps,indent=2)+'\n')
 def stamp(t):
  m=int(round(t*1000));return f'{m//3600000:02}:{(m//60000)%60:02}:{(m//1000)%60:02},{m%1000:03}'
 (S/'renders'/f'{name}.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(caps))+'\n')
 return caps

TEXT={
 'personal':[
 (0,2.7,'WHY I BUILT','SNAP TO LEAGUE','FROM A REAL PROBLEM','Original event footage · Founder’s recorded voice',True,(60,570,960,540),'human'),
 (2.7,3.2,'STILL ON','PAPER.','SCORES SHOULD OUTLIVE THE SHEET','Real handwritten results',False,(60,520,960,960),'picture'),
 (5.9,2.4,'A REAL PROBLEM.','A WEEKEND BUILD.','PHOTO IMPORT + REVIEW','Original event footage · Founder’s recorded voice',False,(60,520,960,960),'picture'),
 (8.3,6.58,'A REAL PROBLEM.','A WEEKEND BUILD.','PHOTO IMPORT + REVIEW','Separate live capture · Demo data',False,(90,520,900,980),'picture'),
 (14.88,3.79,'RESULTS,','MADE READABLE.','A WORKING DEMO','Original on-phone event recording',False,(60,520,960,960),'picture'),
 (18.67,3.83,'YOU REVIEW','THE RESULTS.','PEOPLE STAY IN CONTROL','Separate real capture · Demo data',False,(90,530,900,960),'picture'),
 (22.5,5,'BUILD USEFUL','AI WITH ME.','FOLLOW ANTON','Full demo: YouTube @antonabyzov',True,None,'cta')],
 'easychamp':[
 (0,3.5,'YOUR NEXT RESULT.','ONE PHOTO.','SNAP TO LEAGUE BY EASYCHAMP','Original event footage',True,(60,520,960,960),'picture'),
 (3.5,4.5,'PHOTO','→ REVIEW.','01 / GEMINI EXTRACTION','Real live capture · Demo data',False,(90,520,900,980),'picture'),
 (8,3.6,'CHECK THE NAMES.','CHECK THE SCORE.','02 / YOUR REVIEW','Real editable results · Demo data',False,(90,520,900,980),'picture'),
 (11.6,3.2,'READY','TO SHARE.','03 / EASYCHAMP PUBLISHING','Separate published example · Existing platform',True,(60,630,960,540),'picture'),
 (14.8,6.5,'NEW RESULT?','REVIEW CHANGES.','NEXT / ANOTHER PHOTO','Actual comparison · Demo data',False,(90,520,900,980),'picture'),
 (21.3,3.9,'BUILT AT','SHELLHACKS.','PHOTO IMPORT + REVIEW','On the existing EasyChamp platform',True,(60,570,960,540),'human'),
 (25.2,5.8,'RUN YOUR','NEXT GAME.','FOLLOW EASYCHAMP','Try Snap to League',True,None,'cta')]
}

def htmlcomp(name,total,caps):
 scenes=[];anim=[];wipes=[]
 for i,(t,d,l1,l2,kicker,label,dark,box,kind) in enumerate(TEXT[name]):
  fg='#FAFAFA' if dark else '#22263B';accent='#A4A7FF' if dark else '#595ECC'
  lines=''.join('<span class="mask"><span class="title-line">'+html.escape(x)+'</span></span>' for x in (l1,l2))
  content=f'<div class="title-block"><div class="kicker">{html.escape(kicker)}</div><h1 id="title-{i}">{lines}</h1><div id="rule-{i}" class="rule" style="background:{accent}"></div></div>'
  if kind=='cta':
   label='Full demo: YouTube @antonabyzov' if name=='personal' else 'Try Snap to League'
   content+=f'<div class="endcopy"><div class="ask">{"Follow Anton for real AI builds" if name=="personal" else "Follow EasyChamp"}</div><div class="channel">{label}</div><div class="cta-url"><div id="fill-{i}" class="cta-fill"></div><span>snap.easychamp.com ↗</span></div><p class="credit">Built at ShellHacks on the existing EasyChamp platform.</p></div>'
  else:
   ly=(box[1]+box[3]+28) if box else 1508
   content+=f'<div class="label" style="top:{ly}px">{html.escape(label)}</div>'
   if kind=='human':content+='<div class="human-note">A scoresheet.<br>A phone.<br>A useful AI workflow.</div>'
  if box:
   x,y,w,h=box;content+=f'<svg class="frame" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" viewBox="0 0 {w} {h}"><rect id="stroke-{i}" x="2" y="2" width="{w-4}" height="{h-4}" fill="none" stroke="{accent}" stroke-width="3" pathLength="1"/></svg>'
   anim.append(f'tl.fromTo("#stroke-{i}",{{strokeDasharray:1,strokeDashoffset:1}},{{strokeDashoffset:0,duration:.52,ease:"power2.out",immediateRender:false}},{t+.12});')
  scenes.append(f'<section id="scene-{i}" class="clip scene {kind}" data-start="{t}" data-duration="{d}" data-track-index="2" style="color:{fg}">{content}</section>')
  if i:
   anim.append(f'tl.fromTo("#title-{i} .title-line",{{yPercent:108}},{{yPercent:0,duration:.42,stagger:.065,ease:"power3.out",immediateRender:false}},{t+.09});')
  anim.append(f'tl.fromTo("#rule-{i}",{{scaleX:0}},{{scaleX:1,duration:.48,ease:"power2.out",immediateRender:false}},{t+.12});')
  if kind=='cta':anim.append(f'tl.fromTo("#fill-{i}",{{scaleX:0}},{{scaleX:1,duration:.38,ease:"power2.out",immediateRender:false}},{t+.35});')
  if i and (t in ([2.7,8.3,18.67,22.5] if name=='personal' else [3.5,11.6,14.8,25.2])):
   begin=t-.2;wipes.append(f'<div id="wipe-{i}" class="clip wipe" data-start="{begin}" data-duration=".4" data-track-index="4"><div id="curtain-{i}" class="curtain"></div></div>');anim.append(f'tl.fromTo("#curtain-{i}",{{xPercent:-110,skewX:-5}},{{xPercent:0,duration:.2,ease:"power2.in",immediateRender:false}},{begin});tl.to("#curtain-{i}",{{xPercent:110,duration:.2,ease:"power2.out"}},{t});')
 captions=''.join(f'<div id="cap-{i}" class="clip cap" data-start="{c["start"]}" data-duration="{c["end"]-c["start"]:.3f}" data-track-index="3"><span>{html.escape(c["text"])}</span></div>' for i,c in enumerate(caps))
 brand='ANTON ABYZOV / AI BUILDS' if name=='personal' else 'EASYCHAMP / SNAP TO LEAGUE'
 css='''@font-face{font-family:Archivo;src:url(assets/fonts/archivo-400.ttf)}@font-face{font-family:Archivo;src:url(assets/fonts/archivo-700.ttf);font-weight:700}@font-face{font-family:ArchivoBlack;src:url(assets/fonts/archivo-black-400.ttf);font-weight:900}*{box-sizing:border-box;margin:0;padding:0}html,body{width:100%;height:100%;overflow:hidden;background:#191C31}#root{width:100%;height:100%;position:relative;overflow:hidden;font-family:Archivo,sans-serif}.clip{position:absolute;inset:0}.base{width:100%;height:100%;object-fit:cover}.brand{position:absolute;top:95px;left:62px;color:#FAFAFA;font-size:25px;font-weight:700;letter-spacing:1.6px;background:#595ECC;padding:12px 17px;border-radius:4px;z-index:7}.title-block{position:absolute;top:203px;left:62px;width:936px}.kicker{font-size:23px;font-weight:700;letter-spacing:2px;margin-bottom:25px}h1{font-family:ArchivoBlack,sans-serif;font-size:81px;font-weight:900;line-height:1.02;letter-spacing:-2.5px}h1 span{display:block}.mask{overflow:hidden;padding-bottom:.08em;margin-bottom:-.08em}.title-line{will-change:transform}.rule{height:8px;width:215px;transform-origin:left center;margin-top:29px}.frame{position:absolute;pointer-events:none}.label{position:absolute;left:64px;width:938px;font-size:25px;line-height:1.25}.human-note{position:absolute;left:64px;top:1220px;font-size:48px;font-weight:700;line-height:1.15;letter-spacing:-.6px}.cap{left:64px;right:80px;top:1570px;bottom:auto;min-height:90px;display:flex;justify-content:center;align-items:center;z-index:5}.cap span{display:block;color:#FAFAFA;background:#22263B;border:2px solid #8186F1;border-radius:12px;padding:15px 23px;font-size:45px;font-weight:700;line-height:1.12;text-align:center;max-width:936px}.wipe{overflow:hidden;z-index:6}.curtain{position:absolute;inset:0 -15%;background:#595ECC;border-right:8px solid #A4A7FF}.folio{position:absolute;left:64px;bottom:174px;font-size:21px;letter-spacing:2px;background:#343950;color:#FAFAFA;padding:6px 10px;z-index:8}.progress{position:absolute;bottom:0;left:0;width:100%;height:7px;background:#8186F1;transform-origin:left center;z-index:9}.endcopy{position:absolute;left:65px;right:70px;top:725px}.ask{font-size:47px;line-height:1.18;font-weight:700;max-width:860px}.channel{font-size:32px;line-height:1.3;margin-top:35px}.cta-url{position:relative;font-size:49px;font-weight:700;margin-top:72px;padding:27px 25px;border-radius:10px;overflow:hidden;color:#191C31;white-space:nowrap}.cta-url span{position:relative}.cta-fill{position:absolute;inset:0;background:#A4A7FF;transform-origin:left center}.credit{font-size:29px;line-height:1.35;max-width:850px;margin-top:105px}.cta h1{font-size:99px;line-height:1.05}.cta .title-block{top:245px}'''
 doc=f'<!doctype html><html lang="en"><head><meta charset="utf-8"><script src="assets/vendor/gsap.min.js"></script><style>{css}</style></head><body><div id="root" data-composition-id="{name}" data-start="0" data-duration="{total}" data-width="1080" data-height="1920" data-fps="30"><video id="picture" class="clip base" src="assets/footage/{name}-base.mp4" data-start="0" data-duration="{total}" data-track-index="0" muted playsinline></video><audio id="narration" src="assets/audio/{name}-voice.wav" data-start="0" data-duration="{total}" data-track-index="1"></audio><audio id="music-bed" src="assets/audio/{name}-music.wav" data-start="0" data-duration="{total}" data-track-index="5"></audio>'+''.join(scenes+wipes)+captions+f'<div class="brand">{brand}</div><div class="folio">SHELLHACKS 2026</div><div id="progress" class="progress"></div></div><script>const tl=gsap.timeline({{paused:true}});'+''.join(anim)+f'tl.fromTo("#progress",{{scaleX:0}},{{scaleX:1,duration:{total},ease:"none"}},0);window.__timelines=window.__timelines||{{}};window.__timelines["{name}"]=tl;</script></body></html>'
 # Public reproduction uses the finished approved mix when available.
 if (A/'audio'/f'{name}-final.wav').exists():
  import re
  aud=re.findall(r'<audio\b[^>]*>.*?</audio>',doc,flags=re.S)
  doc=doc.replace(aud[0],f'<audio id="finished-mix" src="assets/audio/{name}-final.wav" data-start="0" data-duration="{total}" data-track-index="1"></audio>').replace(aud[1],'')
 (S/name/'index.html').write_text(doc)
 if not (S/name/'assets').exists():(S/name/'assets').symlink_to('../assets',target_is_directory=True)

if __name__=='__main__':
 for name,seq,total in [('personal',PERSONAL,27.5),('easychamp',PRODUCT,31.0)]:
  with ThreadPoolExecutor(max_workers=3) as pool:files=list(pool.map(shot,[(name,i,s) for i,s in enumerate(seq)]))
  listing=S/'.private'/f'{name}-concat.txt';listing.write_text('\n'.join("file '"+str(p)+"'" for p in files)+'\n')
  run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',listing,'-c','copy','-movflags','+faststart',A/'footage'/f'{name}-base.mp4'])
  caps=audio(name,total);htmlcomp(name,total,caps);print(name,'picture/audio/captions ready',flush=True)
 (S/'reports/source-provenance.json').write_text(json.dumps({'personal_duration':27.5,'easychamp_duration':31,'picture_bases':{n:sha(A/'footage'/f'{n}-base.mp4') for n in ['personal','easychamp']},'9061':{'original_name':'139APPLE_IMG_9061.MOV','source_in':.1,'source_out':1.7,'native_HLG_to_BT709':'avconvert Preset1920x1080','crop':'1080:1080:440:0','audio':'excluded','grade':'conservative shadow curve matching accepted 9062 grade','asset_sha256':sha(phone)},'9062':{'source_in':4.15,'source_out':6.55,'audio':'excluded: unrelated venue TV','privacy':'baked tracked badge blur','grade':'accepted v2 conservative shadow grade','asset_sha256':sha(A/'footage/9062-drift-safe-graded.mp4')},'synthetic_voice':{'personal':False,'easychamp':True,'model':'eleven_v3','voice_id':'EXAVITQu4vr4xnSDxMaL'},'music':{'title':'Deep Urban','artist':'Eugenio Mininni','source':'https://assets.mixkit.co/music/623/623.mp3','license':'Mixkit Stock Music Free License','sha256':sha(A/'audio/deep-urban.mp3')}},indent=2)+'\n')
