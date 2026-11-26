# Deck source

`build.js` builds `../beyond-the-scan.pptx` with [pptxgenjs](https://gitbrent.github.io/PptxGenJS/): OVI's warm neutrals, Georgia titles, Helvetica Neue text and the OVI halftone ball as the one motif. Speaker notes live in `notes.json`.

```bash
npm install pptxgenjs        # in this folder, once
node build.js                # writes ../beyond-the-scan.pptx
node sphere.js ../../../frontend/public/ovi-logo.svg sphere.png   # redraw the halftone ball (2400px)
```
