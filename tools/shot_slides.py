import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
from PIL import Image
t=open('slides.tpl.html').read().replace('{{ROSETTE}}',open('rosette.html').read()).replace('{{ORG}}','50.195% 43.978%')
open('www/slides.html','w').write(t)
srv=subprocess.Popen([sys.executable,'-m','http.server','8767','-d','www'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(1)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
    pg=await b.new_page(viewport={'width':4320,'height':1440})
    errs=[]; pg.on('console',lambda m: errs.append(m.text) if m.type=='error' else None)
    await pg.goto('http://localhost:8767/slides.html'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(800)
    await pg.screenshot(path='pano.png'); print('errors',errs)
    await b.close()
asyncio.run(main()); srv.terminate()
im=Image.open('pano.png').convert('RGB')
for i in range(4):
  im.crop((i*1080,0,(i+1)*1080,1440)).save(f'out/kaleidoscope-0{i+2}.png')
im.resize((2160,720)).save('pano_small.png')
