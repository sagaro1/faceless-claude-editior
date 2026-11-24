import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, random, spring, staticFile, Easing} from 'remotion';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Montserrat';
import {Character, Expr, Fx, Outfit, Pose, Prop} from './Character';

const {fontFamily} = loadFont('normal', {weights: ['800', '900']});

/*
 * Story engine: one storyboard.json + one timeline.json (from dialogue_voice.py) -> a finished Short.
 * Time specs: @12.3 absolute | 1.5 seconds after shot start | w:word(+/-off) first matching word at/after
 * shot start | L3 / L3e (+/-off) line 3 start / end.
 */

type Word = {text: string; start: number; end: number; line: number};
type Line = {speaker: string; text: string; start: number; end: number};
type Cue = {start: number; end: number; value: string};
type Spec = string | number;
type Key = {t: Spec; x?: number; y?: number; s?: number; r?: number; vis?: number; expr?: Expr; pose?: Pose; prop?: Prop | null; face?: 'L' | 'R'; fx?: Fx | null};
type CharSpec = {id: Outfit; track: Key[]};
type Obj = {type: 'door' | 'cash' | 'sign' | 'hand'; rect?: number[]; open?: Spec; color?: string; glow?: string; x?: number; y?: number; at?: Spec; text?: string};
type Cam = {zoom?: number[]; pan?: number[]; rot?: number[]; origin?: number[]; shake?: number};
type ShotSpec = {start: Spec; bg: string; cam: string | Cam; trans?: 'dissolve'; chars: CharSpec[]; objects?: Obj[]; sfx?: {id: string; at: Spec; vol?: number}[]};

const FPS = 30;
const WORLD = 1920;
const k = WORLD / 1024;
const ease = Easing.inOut(Easing.quad);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');
const SPEAKER: Record<Outfit, string> = {leo: 'LEO', baker: 'BAKER', sam: 'SAM', engineer: 'ENGINEER', boss: 'BOSS', watermelon: 'WATERMELON', pineapple: 'PINEAPPLE', miner: 'MINER', digger: 'DIGGER'};

/** Giant cartoon hand that swoops in from the top-right and points down-left. */
const Hand: React.FC<{at: number; t: number}> = ({at, t}) => {
  if (t < at) return null;
  const p = spring({frame: Math.round((t - at) * FPS), fps: FPS, config: {damping: 13, stiffness: 120}});
  const tap = Math.sin((t - at) * 10) * 10 * Math.min(1, (t - at) / 0.6);
  return (
    <svg viewBox="0 0 400 400" width={640} height={640}
      style={{position: 'absolute', left: 560 + (1 - p) * 600, top: 360 - (1 - p) * 700 + tap, transform: 'rotate(35deg)'}}>
      <path d="M150 400 L150 230 Q150 200 175 200 L175 60 Q175 30 200 30 Q225 30 225 60 L225 190 Q260 180 270 205 Q300 195 310 222 Q340 215 345 245 L345 320 Q345 400 270 400 Z"
        fill="#f4c7a1" stroke="#1b1b24" strokeWidth={10} strokeLinejoin="round" transform="rotate(180 250 215)" />
    </svg>
  );
};

const LEGACY_CAM: Record<string, Cam> = {
  panL: {pan: [160, -160]}, panR: {pan: [-160, 160]}, zoomIn: {zoom: [1, 1.12]}, slowZoom: {zoom: [1, 1.25]}, none: {},
};

export const makeShort = (timeline: any, storyboard: any, dir: string, opts: {captionY?: number; music?: number; videoBg?: string} = {}) => {
  const words = timeline.words as Word[];
  const lines = timeline.lines as Line[];
  const mouth = timeline.mouth as Record<string, Cue[]>;
  const END = lines[lines.length - 1].end + 0.35;

  const resolve = (spec: Spec, base: number): number => {
    if (typeof spec === 'number') return base + spec;
    const m = spec.match(/^(.*?)([+-]\d*\.?\d+)?$/)!;
    const head = m[1];
    const off = m[2] ? parseFloat(m[2]) : 0;
    if (head.startsWith('@')) return parseFloat(head.slice(1)) + off;
    const lm = head.match(/^L(\d+)(e?)$/);
    if (lm) return (lm[2] ? lines[+lm[1]].end : lines[+lm[1]].start) + off;
    if (head.startsWith('w:')) {
      const target = norm(head.slice(2));
      const w = words.find((x) => norm(x.text) === target && x.start >= base - 0.05);
      if (!w) throw new Error(`[${dir}] word "${target}" not found after ${base.toFixed(2)}s`);
      return w.start + off;
    }
    throw new Error(`bad time spec ${spec}`);
  };

  const shots: (ShotSpec & {t0: number})[] = [];
  for (const s of storyboard.shots as ShotSpec[]) {
    const prev = shots.length ? shots[shots.length - 1].t0 : 0;
    shots.push({...s, t0: resolve(s.start, prev)});
  }
  const shotEnd = (i: number) => (i + 1 < shots.length ? shots[i + 1].t0 : END);
  const mouthAt = (speaker: string, t: number) => (mouth[speaker] ?? []).find((c) => t >= c.start && t < c.end)?.value;

  const evalTrack = (track: Key[], base: number, t: number) => {
    const keys = track.map((kf) => ({...kf, time: resolve(kf.t, base)})).sort((a, b) => a.time - b.time);
    const num = (field: 'x' | 'y' | 's' | 'r' | 'vis', dflt: number) => {
      const ks = keys.filter((kf) => kf[field] !== undefined);
      if (!ks.length) return {v: dflt, moving: 0};
      if (t <= ks[0].time) return {v: ks[0][field]!, moving: 0};
      for (let i = 0; i < ks.length - 1; i++) {
        const a = ks[i], b = ks[i + 1];
        if (t >= a.time && t < b.time) {
          const p = ease((t - a.time) / Math.max(1e-3, b.time - a.time));
          return {v: a[field]! + (b[field]! - a[field]!) * p, moving: Math.sign(b[field]! - a[field]!)};
        }
      }
      return {v: ks[ks.length - 1][field]!, moving: 0};
    };
    const step = <F extends 'expr' | 'pose' | 'prop' | 'face' | 'fx'>(field: F) => {
      let v: Key[F] | undefined, since = base;
      for (const kf of keys) if (kf.time <= t && field in kf) { v = kf[field]; since = kf.time; }
      return {v, since};
    };
    const x = num('x', 0.5), y = num('y', 1640);
    const pose = step('pose'), fx = step('fx');
    return {
      x: x.v, y: y.v, s: num('s', 1).v, r: num('r', 0).v, vis: num('vis', 1).v,
      walking: x.moving !== 0 || y.moving !== 0, dir: x.moving,
      expr: (step('expr').v ?? 'neutral') as Expr,
      pose: (pose.v ?? 'idle') as Pose, poseT: t - pose.since,
      prop: (step('prop').v ?? undefined) as Prop,
      face: step('face').v,
      fx: (fx.v ?? undefined) as Fx, fxT: t - fx.since,
    };
  };

  // ---------- world pieces ----------
  const Door: React.FC<{o: Obj; base: number; t: number}> = ({o, base, t}) => {
    const openAt = resolve(o.open!, base);
    if (t < openAt) return null;
    const p = interpolate(t, [openAt, openAt + 0.45], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
    const [x0, y0, x1, y1] = o.rect!.map((v) => v * k);
    return (
      <>
        <div style={{position: 'absolute', left: x0, top: y0, width: x1 - x0, height: y1 - y0,
          background: `radial-gradient(ellipse at 50% 70%, ${o.glow}, #6b3a12 90%)`, boxShadow: `0 0 ${60 * p}px ${o.glow}`}} />
        <div style={{position: 'absolute', left: x0, top: y0, width: x1 - x0, height: y1 - y0, transformOrigin: 'left center',
          transform: `perspective(900px) rotateY(${-78 * p}deg)`, background: o.color, border: '6px solid rgba(0,0,0,.35)', boxSizing: 'border-box'}}>
          <div style={{position: 'absolute', left: '30%', top: '18%', width: '40%', aspectRatio: '1', borderRadius: '50%', background: 'rgba(40,60,50,.8)'}} />
        </div>
      </>
    );
  };

  const CashPile: React.FC<{x: number; y: number}> = ({x, y}) => (
    <svg viewBox="0 0 200 110" width={200} height={110} style={{position: 'absolute', left: x - 100, top: y - 100}}>
      <ellipse cx={100} cy={100} rx={95} ry={10} fill="#000" opacity={0.3} />
      {[0, 1, 2, 3, 4].map((i) => <rect key={i} x={20 + (i % 2) * 8} y={78 - i * 15} width={160} height={22} rx={3} fill="#4caf50" stroke="#1d5e20" strokeWidth={3} />)}
      <rect x={88} y={18} width={24} height={82} fill="#f2b705" opacity={0.85} />
    </svg>
  );

  const Sign: React.FC<{text: string; at: number; t: number}> = ({text, at, t}) => {
    const s = t < at ? 0 : spring({frame: Math.round((t - at) * FPS), fps: FPS, config: {damping: 9, stiffness: 180}});
    return (
      <div style={{position: 'absolute', top: 250, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${s}) rotate(${Math.sin(t * 3) * 2}deg)`}}>
        <div style={{background: '#8b5a2b', border: '10px solid #5c3a1a', borderRadius: 18, padding: '26px 46px', fontFamily, fontWeight: 900, fontSize: 66,
          color: '#fff6d5', textAlign: 'center', lineHeight: 1.1, maxWidth: 760, boxShadow: '0 20px 40px rgba(0,0,0,.45)'}}>{text}</div>
      </div>
    );
  };

  // ---------- shot ----------
  const Shot: React.FC<{i: number; t: number; opacity?: number}> = ({i, t, opacity = 1}) => {
    const shot = shots[i];
    const base = shot.t0, end = shotEnd(i);
    const cam: Cam = typeof shot.cam === 'string' ? LEGACY_CAM[shot.cam] ?? {} : shot.cam ?? {};
    const p = ease(interpolate(t, [base, end], [0, 1], clamp));
    const lerp = (r: number[] | undefined, d: number) => (r ? r[0] + (r[1] - r[0]) * p : d);
    const zoom = lerp(cam.zoom, 1), pan = lerp(cam.pan, 0), rot = lerp(cam.rot, 0);
    const [ox, oy] = cam.origin ?? [0.5, 0.5];
    const f = Math.round(t * FPS);
    const shakeAmt = (cam.shake ?? 0) * interpolate(t - base, [0, 0.6], [22, 6], clamp);
    const sx = (random(`sx${f}`) - 0.5) * shakeAmt, sy = (random(`sy${f}`) - 0.5) * shakeAmt;
    const punch = shot.trans === 'dissolve' ? 1 : interpolate(t - base, [0, 0.18], [1.06, 1], clamp);
    const wx = (x: number) => (WORLD - 1080) / 2 + x * 1080;

    return (
      <AbsoluteFill style={{opacity, transformOrigin: `${ox * 100}% ${oy * 100}%`, transform: `translate(${sx}px, ${sy}px) scale(${zoom * punch}) rotate(${rot}deg)`}}>
        <div style={{position: 'absolute', left: -(WORLD - 1080) / 2 + pan, top: 0, width: WORLD, height: WORLD}}>
          <Img src={staticFile(`${dir}/bg/${shot.bg}.jpg`)} style={{position: 'absolute', width: WORLD, height: WORLD}} />
          {(shot.objects ?? []).map((o, n) =>
            o.type === 'door' ? <Door key={n} o={o} base={base} t={t} /> :
            o.type === 'cash' && t >= resolve(o.at!, base) ? <CashPile key={n} x={wx(o.x!)} y={o.y!} /> : null)}
          {shot.chars.map((c, n) => {
            const st = evalTrack(c.track, base, t);
            if (st.vis <= 0.01) return null;
            const h = 760 * st.s;
            const flip = st.walking && st.dir !== 0 ? st.dir < 0 : st.face === 'L';
            return (
              <div key={n} style={{position: 'absolute', width: h * 0.53, height: h, left: wx(st.x) - h * 0.265, top: st.y - h * 0.953,
                opacity: st.vis, transformOrigin: '50% 95%', transform: `rotate(${st.r}deg)`}}>
                <Character outfit={c.id} expr={st.expr} t={t} talkShape={mouthAt(SPEAKER[c.id], t)} prop={st.prop} flip={flip}
                  pose={st.pose} poseT={st.poseT} walk={st.walking ? t * 11 : null} fx={st.fx} fxT={st.fxT} />
              </div>
            );
          })}
        </div>
        {(shot.objects ?? []).filter((o) => o.type === 'sign').map((o, n) => <Sign key={n} text={o.text!} at={resolve(o.at!, base)} t={t} />)}
        {(shot.objects ?? []).filter((o) => o.type === 'hand').map((o, n) => <Hand key={n} at={resolve(o.at!, base)} t={t} />)}
      </AbsoluteFill>
    );
  };

  // ---------- audio ----------
  const sfxEvents = shots.flatMap((s) => (s.sfx ?? []).map((e) => ({id: e.id, at: resolve(e.at, s.t0), vol: e.vol ?? 0.8})));
  const stepEvents: number[] = [];
  shots.forEach((s, i) => {
    for (const c of s.chars) for (let t = s.t0; t < shotEnd(i); t += 0.3) {
      const st = evalTrack(c.track, s.t0, t);
      if (st.walking && st.vis > 0.3) stepEvents.push(t);
    }
  });
  const stingAt = [...sfxEvents].reverse().find((e) => e.id === 'sting')?.at ?? END;
  const musicVol = opts.music ?? 0.13;

  const SoundTrack = () => (
    <>
      <Audio src={staticFile(`${dir}/voice.mp3`)} />
      <Sequence from={0} durationInFrames={Math.max(1, Math.round(stingAt * FPS))} layout="none">
        <Audio src={staticFile('sfx/bed.wav')}
          volume={(f) => interpolate(f, [0, 8, stingAt * FPS - 10, stingAt * FPS], [0, musicVol, musicVol, 0], clamp)} />
      </Sequence>
      {sfxEvents.map((e, n) => (
        <Sequence key={`s${n}`} from={Math.round(e.at * FPS)} layout="none">
          <Audio src={staticFile(`sfx/${e.id}.wav`)} volume={e.vol} />
        </Sequence>
      ))}
      {stepEvents.map((at, n) => (
        <Sequence key={`f${n}`} from={Math.round(at * FPS)} durationInFrames={6} layout="none">
          <Audio src={staticFile('sfx/step.wav')} volume={0.45} />
        </Sequence>
      ))}
    </>
  );

  // ---------- captions ----------
  type Chunk = {words: Word[]; start: number; end: number};
  const chunks: Chunk[] = [];
  for (const w of words) {
    const last = chunks[chunks.length - 1];
    const brk = !last || last.words.length >= 2 || last.words[0].line !== w.line || /[.,!?]$/.test(last.words[last.words.length - 1].text) || norm(w.text).length > 8;
    if (brk) chunks.push({words: [w], start: w.start, end: w.end});
    else { last.words.push(w); last.end = w.end; }
  }
  const Captions: React.FC<{t: number}> = ({t}) => {
    const i = chunks.findIndex((c, n) => t >= c.start && (n === chunks.length - 1 || t < chunks[n + 1].start));
    if (i < 0 || t > chunks[i].end + 0.4) return null;
    const c = chunks[i];
    const pop = spring({frame: Math.round((t - c.start) * FPS), fps: FPS, config: {damping: 15, stiffness: 260}});
    const speaker = lines[c.words[0].line].speaker;
    return (
      <div style={{position: 'absolute', top: opts.captionY ?? 1430, width: '100%', textAlign: 'center', transform: `scale(${0.85 + 0.15 * pop})`,
        fontFamily, fontWeight: 800, fontSize: 74, color: speaker === 'NARRATOR' ? '#fff' : '#ffe066',
        textShadow: '0 4px 14px rgba(0,0,0,.85), 0 0 4px rgba(0,0,0,.9)'}}>
        {c.words.map((w) => w.text).join(' ')}
      </div>
    );
  };

  const Comp = () => {
    const frame = useCurrentFrame();
    const {fps} = useVideoConfig();
    const t = frame / fps;
    const i = shots.findIndex((s, n) => t >= s.t0 && t < shotEnd(n));
    const dissolving = i > 0 && shots[i].trans === 'dissolve' && t - shots[i].t0 < 0.35;
    if (opts.videoBg) {
      // 3D mode: picture comes from the Blender render; we add captions, overlays and all audio
      const shot = i >= 0 ? shots[i] : null;
      return (
        <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
          <SoundTrack />
          <OffthreadVideo src={staticFile(opts.videoBg)} muted style={{width: 1080, height: 1920}} />
          {shot && (shot.objects ?? []).filter((o) => o.type === 'hand').map((o, n) => <Hand key={n} at={resolve(o.at!, shot.t0)} t={t} />)}
          {t < END && <Captions t={t} />}
        </AbsoluteFill>
      );
    }
    return (
      <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
        <SoundTrack />
        {t < END && dissolving && <Shot i={i - 1} t={t} />}
        {t < END && i >= 0 && <Shot i={i} t={t} opacity={dissolving ? (t - shots[i].t0) / 0.35 : 1} />}
        <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 45%, transparent 55%, rgba(0,0,0,.45))'}} />
        {t < END && <Captions t={t} />}
      </AbsoluteFill>
    );
  };

  return {Comp, END};
};
