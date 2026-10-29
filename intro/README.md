# Intro figure

`intro.html` (in the repository root) is the explainer the app opens with: the Space Shuttle preset from the Build screen as a wind-tunnel model on a pitch sector. Hover it, tap it or use the arrow keys, and its upper skin, wing skins, nose cap, payload container and engines come away. Underneath is the structure the builder lays out for that design: frames and bulkheads, keel, chines and bay sills, the crew module, the tanks on their deck, and the wing spars and ribs.

It is drawn with [Anatomy](https://github.com/wheresryan22/anatomy) (MIT), an isometric figure kit. Every size comes from `shuttle.json`, the Shuttle preset's CAD package (`cad/*.design.json` format).

To rebuild it, put this folder at `examples/spaceplane/` in a checkout of Anatomy, then run:

```sh
node build.mjs --osp            # writes intro.html in the app's own theme; copy it to the repo root
node build.mjs --osp --audit    # also runs Anatomy's geometry and depth-order audit
node build.mjs --quick --osp    # skips the depth settle, for quick looks
```

- `--light` writes the light theme instead.
- `?theme=light|dark|osp` picks a theme at run time.
- `?embed=1` trims the page for the app's intro dialog and reports the page's height to it.

The app shows the intro on first load. Choosing "Don't show this again" stores `vwt.intro = 0`. The "What is this?" link under the title opens it again, and `?intro=1` or `?intro=0` in the address forces it on or off.
