"""Build truthful editorial picture/speech tracks and timed-caption source.

Real captured UI is never reconstructed. Source time is original camera time.
The assembled base contains one video per output to avoid multi-video render bugs.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, subprocess, os, hashlib

P=Path(__file__).resolve().parents[1]
F=P/'assets/footage'; A=P/'assets/audio'; E=P/'editorial'
E.mkdir(exist_ok=True)
TRANS=Path(os.environ.get('SNAP_TRANSCRIPTS',str(P/'.private/transcripts')))
OFF={'9045':28,'9051':5,'9056':16,'9034':1}

# start, length, original audio source, source time, picture, framing, heading, subheading
LAND=[
 (0,2.4,'9043',.8,'9043','founder','YOUR LEAGUE.\nSTILL ON PAPER?','A weekend idea, born at ShellHacks.'),
 (2.4,5.4,'9043',5.8,'9034','event','OFFICE CUPS.\nSCHOOL LEAGUES.','And the games between hackathon sessions.'),
 (7.8,3.2,'9045',30.14,'9051','paper','EVERY RESULT.\nONE PIECE OF PAPER.','The problem starts after the final whistle.'),
 (11,8.98,'9045',35.52,'9051','paper','MEET\nSNAP TO LEAGUE.','Photo → review → share.'),
 (19.98,4,'9049',11.6,'9051','phone','01 / SNAP','Take a photo. Or choose one.'),
 (23.98,10.42,'bridge-a',0,'import','proof','02 / READ + CHECK','Real live capture · demo data'),
 (34.4,3.5,'9049',49.85,'9049','phone','THE GAMES\nBECOME RESULTS.','Original on-phone demo'),
 (37.9,3.79,'9049',57.16,'9049','phone','GROUPS.\nSTANDINGS.','Original on-phone demo'),
 (41.69,8.21,None,0,'review','proof','03 / REVIEW','Names flagged. Scores editable. You stay in control.'),
 (49.9,6,None,0,'group','wide','READY TO SHARE.','Separate published example · Existing EasyChamp platform'),
 (55.9,1.94,'9049',63.2,'9049','phone','GIVE RESULTS\nA VOICE.','Read aloud with ElevenLabs'),
 (57.84,10.55,'9049',66.8,'9049','phone','LISTEN TO\nTHE STANDINGS.','Actual in-product audio · Original event recording'),
 (68.39,5.02,'9056',17.1,'snap-bracket','phone','THE GAMES.\nTHE BRACKET.','Separate live capture · Demo data'),
 (73.41,2.59,None,0,'bracket','wide','THE WHOLE BRACKET.','Separate published example · Existing EasyChamp platform'),
 (76,7.78,'9060',17.12,'9060','phone','PAPER OR SCREEN.\nSAME STARTING POINT.','Real handwritten input, captured at ShellHacks.'),
 (83.78,3,None,0,'9034','event','MORE WAYS\nTO COMPETE.','ShellHacks activity'),
 (86.78,2,None,0,'trivia','wide','ANYTHING\nWITH PLACES.','Real Snap demo · Podiums share on Snap'),
 (88.78,15.22,'bridge-b',0,'update','proof','NEW RESULT?\nADD ANOTHER PHOTO.','Live comparison · Demo data'),
 (104,6,None,0,'9051','end','PLAY THE GAME.\nKEEP THE STORY.','snap.easychamp.com'),
]
VERT=[
 (0,3.2,'9045',30.14,'9051','paper','STILL TRACKING\nSCORES ON PAPER?','Snap to League'),
 (3.2,4,'9049',11.6,'9051','phone','SNAP THE BOARD.','Photo → review → share'),
 (7.2,10.42,'bridge-a',0,'import','proof','LET AI READ IT.\nYOU REVIEW IT.','Live capture · Demo data'),
 (17.62,3.79,'9049',57.16,'9049','phone','SEE THE\nSTANDINGS.','Original on-phone demo'),
 (21.41,5.02,'9056',17.1,'snap-bracket','phone','SEE THE\nBRACKET.','Separate live capture · Demo data'),
 (26.43,3.72,'9049',66.96,'9049','phone','HEAR THE\nRESULTS.','Actual in-product audio · ElevenLabs'),
 (30.15,6.35,None,0,'9051','end','PLAY THE GAME.\nKEEP THE STORY.','snap.easychamp.com'),
]

def command(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 if p.returncode:raise RuntimeError(' '.join(map(str,args[:7]))+'\n'+p.stderr[-5000:])
 return p.stdout

def source_info(s):
 start,dur,a,at,pic,style,*_=s
 if pic in ('import','review','update'):
  desk=P/'assets/proof/desktop-live-import-and-update.mp4'
  # Real-time input capture; never accelerate or fabricate an interaction.
  if desk.exists():
   timing=json.loads((P/'reports/desktop-proof-timeline.json').read_text())
   t={x['event']:x['atSeconds'] for x in timing}
   offset={'import':t['read clicked']-.3,'review':t['review visible'], 'update':t['update read clicked']-.3}[pic]
   return desk,offset,False,None
  f={'import':'04-review-phone.png','review':'05-warning-phone.png','update':'10-update-comparison-phone.png'}[pic]
  return P/'assets/proof'/f,0,True,(0,0,860,1120)
 if pic=='snap-bracket':return P/'assets/proof/14-snap-knockout-desktop.png',0,True,(792,62,514,367)
 if pic=='trivia':return P/'assets/proof/11-trivia-desktop.png',0,True,(120,65,680,680)
 if pic in ('group','bracket'):
  return P/'assets/proof'/f'11-{pic}-desktop-v2.png',0,True,None
 if pic=='9051':return F/'9051-sdr.mp4',3.2 if start==11 else 0,False,(260,0,1660,1000)
 if pic=='9034':return F/'9034-sdr.mp4',0,False,None
 crops={'9043':(340,0,1360,760),'9045':(240,0,1480,760),
        '9049':(360,0,1560,950),'9056':(0,0,1500,1040),'9060':(260,0,1600,1050)}
 return F/f'{pic}-sdr.mp4',max(0,at-OFF.get(pic,0)),False,crops.get(pic)

def picture(job):
 name,i,s=job
 t,dur,a,at,pic,style,*_=s
 W,H=(1920,1080) if name=='landscape' else (1080,1920)
 # 30fps boundaries are consistently rounded, preventing cumulative AV drift.
 n=round((t+dur)*30)-round(t*30); seconds=n/30
 dark=style in ('phone','end') or pic in ('group','bracket')
 bg='0x191C31' if dark else '0xF6F6FA'
 if name=='landscape':
  box=(700,168,1132,692) if style not in ('wide','proof') else (566,164,1266,700)
  if style=='end':box=(1060,180,772,660)
 else:
  box=(60,550,960,960)
  if style=='end':box=(60,700,960,700)
 src,ss,still,crop=source_info(s)
 out=E/f'{name}-{i:02d}.mp4'
 cache=out.with_suffix('.cache.json')
 signature=hashlib.sha256(json.dumps({'source':str(src),'mtime_ns':src.stat().st_mtime_ns,'size':src.stat().st_size,'start':ss,'crop':crop,'box':box,'scene':s,'aspect':name,'recipe':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},sort_keys=True).encode()).hexdigest()
 if out.exists() and cache.exists() and json.loads(cache.read_text()).get('signature')==signature:return str(out)
 args=['ffmpeg','-y','-v','error','-filter_complex_threads','2']
 if still:args+=['-loop','1']
 else:args+=['-ss',str(ss)]
 args+=['-i',str(src),'-f','lavfi','-i',f'color=c={bg}:s={W}x{H}:r=30:d={seconds}']
 x,y,w,h=box
 if name=='vertical' and a=='9049' and 57<=at<=61:crop=(220,0,1080,1080)
 if name=='vertical' and a=='9049' and 66<=at<=78:crop=(500,0,1080,1080)
 chain=''
 if crop:
  cx,cy,cw,ch=crop;chain+=f'crop={cw}:{ch}:{cx}:{cy},'
 # Portrait proof displays a cropped real viewport at large readable size.
 if name=='vertical' and pic in ('import','review','update'):
  src2=P/'assets/proof/portrait-clean-live-import-and-update-2x.mp4'
  args=['ffmpeg','-y','-v','error','-filter_complex_threads','2','-ss','3.55','-i',str(src2),'-f','lavfi','-i',f'color=c={bg}:s={W}x{H}:r=30:d={seconds}']
  chain='crop=860:1050:0:100,'
 elif name=='vertical' and style in ('phone','paper') and pic!='snap-bracket':
  # Fill with purposeful center detail, never tiny landscape UI.
  chain += f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},'
 chain+=f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg},setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds},setpts=PTS-STARTPTS'
 # No badges/gallery survive these framing windows; separate selected stills remain truthful.
 filt=f'[0:v]{chain}[shot];[1:v][shot]overlay={x}:{y}:shortest=1,format=yuv420p[v]'
 if name=='landscape' and i==0:
  args+=['-ss','57.16','-i',str(F/'9049-sdr.mp4')]
  filt=f'[0:v]{chain}[shot];[1:v][shot]overlay={x}:{y}:shortest=1[first];[2:v]crop=1560:950:360:0,scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={bg},setsar=1,fps=30,setpts=PTS-STARTPTS[proof];[first][proof]overlay={x}:{y}:enable=gte(t\\,1):shortest=1,format=yuv420p[v]'
 args+=['-filter_complex',filt,'-map','[v]','-an','-frames:v',str(n),'-c:v','libx264','-preset','fast','-crf','17','-threads','4','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(out)]
 command(args);cache.write_text(json.dumps({'signature':signature})+'\n');print(out.name,flush=True);return str(out)

def words(s):
 t,dur,a,at,*_=s
 if a=='9056':dur=min(dur,3.15)
 if not a:return []
 if a.startswith('bridge'):
  d=json.loads((A/f'{a}.json').read_text());q=d.get('normalized_alignment') or d['alignment'];ws=[];word='';st=0;end=0
  for c,b,e in zip(q['characters'],q['character_start_times_seconds'],q['character_end_times_seconds']):
   if c.isspace():
    if word:ws.append({'text':word,'start':st+t+.25,'end':end+t+.25});word=''
   else:
    if not word:st=b
    word+=c;end=e
  if word:ws.append({'text':word,'start':st+t+.25,'end':end+t+.25})
  return ws
 d=json.loads((TRANS/f'139APPLE_IMG_{a}-scribe-v2.json').read_text())
 return [{'text':w['text'],'start':max(t,t+w['start']-at),'end':min(t+dur,t+w['end']-at)} for w in d['words'] if w['type']=='word' and w['start']>=at-.01 and w['end']<=at+dur+.01]

def make_audio(name,seq,total):
 tracks=[]
 for i,s in enumerate(seq):
  t,dur,a,at,*_=s
  if a=='9056':dur=min(dur,3.15)
  if not a:continue
  out=E/f'{name}-voice-{i:02d}.wav';tracks.append((out,t))
  if out.exists():continue
  syn=a.startswith('bridge');src=A/f'{a}.mp3' if syn else F/f'{a}-sdr.mp4'
  ss=0 if syn else at-OFF.get(a,0)
  # Minimal noise reduction for venue speech; retain real in-product audio.
  filters='highpass=f=85,lowpass=f=11000,'
  if not syn:filters+='afftdn=nf=-30:nr=7,'
  filters+='loudnorm=I=-17:TP=-2:LRA=9,aresample=48000,afade=t=in:d=0.008'
  if syn:filters+=',adelay=250|250'
  command(['ffmpeg','-y','-v','error','-ss',str(ss),'-i',str(src),'-t',str(dur),'-af',filters,'-ar','48000','-ac','2',str(out)])
 args=['ffmpeg','-y','-v','error','-filter_complex_threads','2']
 for f,_ in tracks:args+=['-i',str(f)]
 fl=[]
 for i,(_,t) in enumerate(tracks):fl.append(f'[{i}:a]adelay={round(t*1000)}|{round(t*1000)}[v{i}]')
 fl.append(''.join(f'[v{i}]' for i in range(len(tracks)))+f'amix=inputs={len(tracks)}:normalize=0:dropout_transition=0,apad=whole_dur={total},atrim=duration={total}[voice]')
 voice=A/f'{name}-voice.wav'
 command(args+['-filter_complex',';'.join(fl),'-map','[voice]','-ar','48000','-ac','2',str(voice)])
 # Licensed bed, stable instrumental section. Static spectral carve plus speech-triggered duck.
 # A true-peak-safe integrated normalization happens in a measured second pass.
 mix=A/f'{name}-mix-pre.wav'
 fl=f'[0:a]asplit=2[v][sc];[1:a]atrim=start=32:duration={total},asetpts=PTS-STARTPTS,highpass=f=50,equalizer=f=1800:t=q:w=0.7:g=-5,equalizer=f=350:t=q:w=1:g=-2,volume=0.13,afade=t=in:d=0.5,afade=t=out:st={total-2}:d=2[bed];[bed][sc]sidechaincompress=threshold=0.015:ratio=10:attack=10:release=450:makeup=1[duck];[v][duck]amix=inputs=2:normalize=0:duration=first,acompressor=threshold=0.18:ratio=3:attack=3:release=100:knee=2.8:makeup=1[m]'
 command(['ffmpeg','-y','-v','error','-i',str(voice),'-i',str(A/'deep-urban.mp3'),'-filter_complex',fl,'-map','[m]','-ar','48000','-ac','2',str(mix)])
 args=['ffmpeg','-hide_banner','-i',str(mix),'-af','loudnorm=I=-14:TP=-1.8:LRA=20:print_format=json','-f','null','-']
 r=subprocess.run(args,capture_output=True,text=True);j=json.JSONDecoder().raw_decode(r.stderr[r.stderr.rfind('{'):])[0];(P/'reports'/f'{name}-mix-measurement.json').write_text(json.dumps(j,indent=2))
 norm='loudnorm=I=-14:TP=-1.8:LRA=20:linear=true:'+':'.join(f'{a}={j[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
 command(['ffmpeg','-y','-v','error','-i',str(mix),'-af',norm,'-ar','48000','-ac','2',str(A/f'{name}-final.wav')])

def captions(name,seq):
 caps=[]
 for s in seq:
  groups=[];batch=[]
  for w in words(s):
   if batch and (len(batch)>=6 or w['start']-batch[-1]['end']>.5 or batch[-1]['text'].endswith(('.', '?', '!'))):
    groups.append(batch);batch=[]
   batch.append(w)
  if batch:groups.append(batch)
  caps.extend({'start':round(b[0]['start'],3),'end':round(min(s[0]+s[1],b[-1]['end']+.25),3),'text':' '.join(w['text'] for w in b)} for b in groups)
 for i,c in enumerate(caps[:-1]):c['end']=round(min(c['end'],caps[i+1]['start']-.01),3)
 (E/f'{name}-captions.json').write_text(json.dumps(caps,indent=2)+'\n')
 def stamp(t):
  ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
 (P/f'{name}.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(caps))+'\n')

def main():
 for name,seq,total in [('landscape',LAND,110),('vertical',VERT,36.5)]:
  (E/f'{name}-edl.json').write_text(json.dumps([dict(zip(['start','duration','audio','source_in','picture','style','heading','subheading'],s)) for s in seq],indent=2)+'\n')
  captions(name,seq)
  with ThreadPoolExecutor(max_workers=2) as pool:paths=list(pool.map(picture,[(name,i,s) for i,s in enumerate(seq)]))
  manifest=E/f'{name}-concat.txt';manifest.write_text('\n'.join("file '"+str(Path(p).name)+"'" for p in paths)+'\n')
  command(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(manifest),'-c','copy','-movflags','+faststart',str(F/f'{name}-base.mp4')])
  make_audio(name,seq,total)
  print(name,'picture, speech, ducked music and captions complete',flush=True)

if __name__=='__main__':main()
