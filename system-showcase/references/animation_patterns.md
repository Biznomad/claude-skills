# Scroll Animation Pattern Catalog

## Design-elevation layer (Dark OLED Luxury — apply on top of the base build)
- **Film grain**: fixed div, SVG feTurbulence data-URI, `opacity:.055;mix-blend-mode:overlay`, 8s steps() jitter. Instant filmic depth.
- **Marquee tickers**: full-bleed strips rotated `-1.2deg`, mono uppercase, duplicated content + `translateX(-50%)` loop. Place after hero and before pricing.
- **Headlight sweep**: absolutely-positioned gradient beam inside the hero `<h1>`, `gsap.to(x:'240%')` once after load-in. Hide in static mode.
- **Asymmetric header rhythm**: alternate sections wrap kick+h2+sub in `.head-off{margin-left:auto;max-width:760px}`.
- **Gradient-stroke feature cards**: `border:1px solid transparent` + two-layer background `padding-box`/`border-box` gradient trick (featured tier, hero job card).
- **CTA shine**: skewed white gradient `::after` sweeping on hover.
- Body font Satoshi (Fontshare CDN) over Archivo fallback; Unbounded display; JetBrains Mono data.
- Real-photo policy: only verified-URL photos; otherwise CSS-cinematic scenes + [IMAGE PROMPT] comment blocks in the HTML head for future art generation.

Exact working patterns from the reference template (`assets/template/index.html`). All assume GSAP 3.12 + ScrollTrigger self-hosted, and the global static-mode guard.

## 0. Static-mode guard (always first)
```js
const STATIC = new URLSearchParams(location.search).has('static')
  || matchMedia('(prefers-reduced-motion: reduce)').matches;
if (STATIC) document.documentElement.classList.add('static');
// CSS side: html.static .rv{opacity:1!important;transform:none!important} + per-pattern overrides
// In static mode: skip ALL gsap/ScrollTrigger init; set final text/values directly.
```
Every pattern below must have a `html.static` CSS override forcing its end state.

## 1. Reveal-on-scroll default (`.rv`)
```css
.rv{opacity:0;transform:translateY(34px)}
```
```js
document.querySelectorAll('section:not(#hero):not(#loop) .rv').forEach(el=>{
  gsap.to(el,{opacity:1,y:0,duration:.9,ease:'power3.out',
    scrollTrigger:{trigger:el,start:'top 88%'}});
});
```
GOTCHA: exclude any PINNED section's elements from the generic reveal — the pinned timeline owns them; double-triggering causes jumps.

## 2. Pinned scroll-scrubbed flow (the centerpiece — max one per page)
Horizontal N-node pipeline; line draws, nodes pop in sequence, pulse dot travels.
```js
const nodes = gsap.utils.toArray('#loop .fnode');
gsap.set(nodes,{opacity:.18,scale:.82,transformOrigin:'center top'});
const tl = gsap.timeline({scrollTrigger:{
  trigger:'#loop .stage', start:'top top', end:'+=2200', pin:true, scrub:.6}});
tl.to('#loop .flowline',{scaleX:1,duration:6,ease:'none'},0)      // line: scaleX 0→1, origin left
  .to('#loop .pulse',{opacity:1,duration:.2},0)
  .to('#loop .pulse',{left:'95.5%',duration:6,ease:'none'},0)     // traveling dot
  .to('#loop .pulse',{opacity:0,duration:.3},5.8);
nodes.forEach((n,i)=> tl.to(n,{opacity:1,scale:1,duration:.5,ease:'back.out(2)'},
  i*(6/nodes.length)+.15));                                        // sequential pops
```
`end:'+=2200'` ≈ scroll distance the story holds. The section wrapper needs `min-height:100vh` flex-centered.

## 3. SVG line draw (converging channels hub)
```js
document.querySelectorAll('.hpath').forEach(p=>{
  const len=p.getTotalLength();
  p.style.strokeDasharray=len; p.style.strokeDashoffset=len;
  gsap.to(p,{strokeDashoffset:0,ease:'none',
    scrollTrigger:{trigger:'.hub',start:'top 80%',end:'top 25%',scrub:.5}});
});
```
Static override: `html.static .hub path{stroke-dashoffset:0!important}` (and JS sets `strokeDasharray='none'`).
Hub layout: 5 channel pills left → curved paths converge → brand node center → output node right. Animate dash-flow on live pages with `stroke-dasharray:5 7` + keyframed `stroke-dashoffset` if a constant "flowing" feel is wanted.

## 4. Count-up numbers
```html
<span data-count="16607">0</span>
```
```js
gsap.fromTo(el,{textContent:0},{textContent:+el.dataset.count,duration:1.6,
  ease:'power2.out',snap:{textContent:1},
  onUpdate(){ el.textContent=(+el.textContent).toLocaleString(); },
  scrollTrigger:{trigger:el,start:'top 88%'}});
```

## 5. Typing bubble (scenario card)
Play-once on enter (NOT scrubbed — typing feels wrong tied to scroll):
```js
ScrollTrigger.create({trigger:'#typebubble',start:'top 80%',once:true,onEnter(){
  gsap.to({i:0},{i:MSG.length,duration:2.6,ease:'none',
    onUpdate(){ el.textContent=MSG.slice(0,Math.round(this.targets()[0].i)); },
    onComplete(){ el.parentElement.classList.add('done'); /* then pop the result chip */ }});
}});
```
Cursor: `.bubble .txt::after{content:"▍";animation:blink 1s infinite}` removed via `.done`.

## 6. Vertical timeline fill (nurture ladder)
```css
.tlfill{transform:scaleY(0);transform-origin:top}
```
```js
gsap.to('.tlfill',{scaleY:1,ease:'none',
  scrollTrigger:{trigger:'.tl',start:'top 75%',end:'bottom 55%',scrub:.5}});
```
Rows themselves use the `.rv` default; each row = numbered dot + WHEN label + message bubble + AUTO/YOU chip.

## 7. Radar sweep + blips (always-on ambience)
Pure CSS — no JS:
```css
.sweep{background:conic-gradient(from 0deg,rgba(255,176,0,.5),transparent 70deg);
  animation:sweep 3.2s linear infinite}
.blip{animation:blipfade 3.2s infinite}  /* staggered delays per blip */
```

## 8. Scan bar + growing part bars
```js
// scanline sweeps a mono VIN box a few times on enter (once:true), then:
document.querySelectorAll('.pbar i').forEach(bar=>{
  gsap.to(bar,{width:bar.dataset.w+'%',duration:1.1,ease:'power3.out',
    scrollTrigger:{trigger:bar,start:'top 90%'}});
});
```
Bar widths = value/maxValue %. Static: `html.static .pbar i{width:var(--w)!important}` with `style="--w:49%"` inline.

## 9. Progress bar + dot-nav section spy
```js
gsap.to('#progress',{width:'100%',ease:'none',scrollTrigger:{
  trigger:document.body,start:'top top',end:'bottom bottom',scrub:.3}});
document.querySelectorAll('#dots a').forEach(a=>{
  ScrollTrigger.create({trigger:a.getAttribute('href'),start:'top 55%',end:'bottom 55%',
    onToggle(st){ if(st.isActive){/* swap .on class */} }});
});
```

## 10. Ambience layer
Fixed grid background (`background-image` two linear-gradients, radial mask) + two blurred drifting orbs (CSS keyframes) + `dotlive` blinking status dot. Cheap, sets the "command center" tone.

## QA gotchas (repeat offenders)
- Headless Chrome `--window-size` height inflates `100vh` → never full-page-screenshot a vh-based page that way; use the browse binary's full-page capture on the `?static` URL.
- Netlify rename: `netlify api updateSite` ignores top-level `name` — nest it: `{"site_id":"…","body":{"name":"…"}}`.
- GSAP object-tween `onUpdate` uses `this.targets()[0]` — never write `onUpdate function(){}` (syntax error).
- Pin spacers make full-page captures show a large gap after the pinned section — expected, not a bug.
