from playwright.sync_api import sync_playwright
import json, sys
flags=['--enable-unsafe-webgpu','--enable-features=Vulkan,WebGPU','--use-vulkan=swiftshader','--use-webgpu-adapter=swiftshader','--disable-vulkan-surface','--ignore-gpu-blocklist','--disable-gpu-watchdog','--disable-features=GPUWatchdog']
cfg = json.loads(sys.argv[1])
with sync_playwright() as p:
    b=p.chromium.launch(args=flags)
    pg=b.new_page(); pg.set_default_timeout(3600000)
    pg.goto('file://' + __import__('os').path.abspath('h.html'))
    print(json.dumps(pg.evaluate("c => run(c)", cfg)), flush=True)
    b.close()
