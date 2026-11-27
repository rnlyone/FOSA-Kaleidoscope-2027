import asyncio, shutil, subprocess, sys, time, os
from playwright.async_api import async_playwright
SITE='/home/claude/kal/site'; T='/home/claude/ig/www'
shutil.rmtree(T,ignore_errors=True); shutil.copytree(SITE,T)
h=open(T+'/index.html').read().replace('https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/','')
h=h.replace('/* ---------- start ---------- */','window.__kal = () => tl;\n/* ---------- start ---------- */')
h=h.replace('</style>','.ctl,.cue,.bar,main>section:not(.hero),footer{display:none!important}\n</style>',1)
open(T+'/index.html','w').write(h)
for f in ['gsap.min.js','ScrollTrigger.min.js']: shutil.copy('/home/claude/npm/node_modules/gsap/dist/'+f,T)
srv=subprocess.Popen([sys.executable,'-m','http.server','8766','-d',T],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
FPS=30; DUR=float(sys.argv[1]) if len(sys.argv)>1 else 9.0
OUT=sys.argv[2] if len(sys.argv)>2 else '/home/claude/ig/frames'
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg=await b.new_page(viewport={'width':1080,'height':1440})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8766/index.html'); await pg.wait_for_function('window.__ready')
    T0=await pg.evaluate('()=>{gsap.ticker.remove(gsap.updateRoot); const t=gsap.ticker.time; window.__kal().restart(); gsap.updateRoot(t); return t}')
    n=int(FPS*DUR)
    for i in range(n):
      await pg.evaluate(f'gsap.updateRoot({T0}+{(i)/FPS})')
      await pg.screenshot(path=f'{OUT}/f{i:04d}.jpg',type='jpeg',quality=95)
    print('frames',n,'errors',errs)
    await b.close()
asyncio.run(main()); srv.terminate()
