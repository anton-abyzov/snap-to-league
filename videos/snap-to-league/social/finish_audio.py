"""Static gain of the completed mix plus an oversampled safety limiter, video unchanged."""
from pathlib import Path
import subprocess,json,re,math,hashlib,shutil
S=Path(__file__).resolve().parent
files={'personal':'personal-ai-builds-1080x1920.mp4','easychamp':'easychamp-photo-results-1080x1920.mp4'}
def run(args):
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[-2500:])
 return r

def measure(p):
 r=run(['ffmpeg','-hide_banner','-i',p,'-af','loudnorm=I=-14.5:TP=-1.5:LRA=9:print_format=json','-f','null','-'])
 return json.loads(re.search(r'\{\s*"input_i".*?\n\}',r.stderr,re.S).group())
def vhash(p):return run(['ffmpeg','-v','error','-i',p,'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-']).stdout.strip().split('=')[-1]
receipts={}
for name,file in files.items():
 dst=S/'renders'/file;src=S/'.private'/f'{name}-before-normalization.mp4'
 if not src.exists():shutil.copyfile(dst,src)
 before=measure(src);gain=-14.5-float(before['input_i']);passes=[]
 for iteration in range(3):
  candidate=S/'.private'/f'{name}-normalized-{iteration}.mp4'
  filt=f'aresample=192000,volume={gain:.6f}dB,alimiter=limit={10**(-1.9/20):.9f}:level=false:attack=5:release=60:latency=true,aresample=48000'
  run(['ffmpeg','-y','-v','error','-i',src,'-map','0:v:0','-map','0:a:0','-c:v','copy','-af',filt,'-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',candidate])
  m=measure(candidate);passes.append({'gain_db':round(gain,6),'filter':filt,'integrated_lufs':float(m['input_i']),'true_peak_dbtp':float(m['input_tp']),'loudness_range_lu':float(m['input_lra'])})
  if abs(float(m['input_i'])+14.5)<=.2 and float(m['input_tp'])<=-1.5:break
  gain+=-14.5-float(m['input_i'])
 else:raise RuntimeError(f'{name}: normalization outside bounded target')
 assert vhash(src)==vhash(candidate),'Video elementary stream changed'
 shutil.copyfile(candidate,dst)
 receipts[name]={'before_integrated_lufs':float(before['input_i']),'before_true_peak_dbtp':float(before['input_tp']),'target_integrated_lufs':-14.5,'ceiling_dbtp':-1.5,'passes':passes,'video_elementary_sha256':vhash(dst),'video_unchanged':True,'final_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size,'scope':'one static gain on combined speech/music and a peak limiter; original ratio preserved except transient peak limiting'}
 print(name,json.dumps(receipts[name]),flush=True)
(S/'reports/audio-finish.json').write_text(json.dumps(receipts,indent=2)+'\n')
