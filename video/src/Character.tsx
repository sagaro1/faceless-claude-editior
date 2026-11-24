import React from 'react';

/**
 * Original round-head cartoon characters for story videos.
 * viewBox 0 0 300 600 — head centre (150,130) r95, feet at y≈570.
 */
export type Expr = 'neutral' | 'smug' | 'laugh' | 'shocked' | 'angry' | 'happy' | 'crazy' | 'determined' | 'worried';
export type Outfit = 'leo' | 'baker' | 'sam' | 'engineer' | 'boss' | 'watermelon' | 'pineapple' | 'miner' | 'digger';

const HEAD_FILL: Partial<Record<Outfit, string>> = {watermelon: '#6cc24a', pineapple: '#f6c33b'};

/** Fruit skin pattern, clipped to the head, drawn under the face. */
const HeadSkin = ({outfit}: {outfit: Outfit}) => {
  if (outfit !== 'watermelon' && outfit !== 'pineapple') return null;
  return (
    <g>
      <clipPath id={`skin-${outfit}`}><circle cx={150} cy={130} r={92} /></clipPath>
      <g clipPath={`url(#skin-${outfit})`}>
        {outfit === 'watermelon'
          ? [-70, -35, 0, 35, 70].map((dx) => (
              <path key={dx} d={`M${150 + dx} 30 q${-14 + dx * 0.1} 25 0 50 q14 25 0 50 q-14 25 0 50 q14 25 0 50`}
                stroke="#2e7d32" strokeWidth={14} fill="none" strokeLinecap="round" opacity={0.85} />
            ))
          : (
            <g stroke="#c8811a" strokeWidth={4} opacity={0.75}>
              {[-120, -80, -40, 0, 40, 80, 120, 160].map((d) => (
                <g key={d}>
                  <line x1={60 + d} y1={30} x2={240 + d} y2={230} />
                  <line x1={240 - d} y1={30} x2={60 - d} y2={230} />
                </g>
              ))}
            </g>
          )}
        {/* lighter face area so expressions stay readable */}
        <ellipse cx={150} cy={160} rx={70} ry={62} fill={outfit === 'watermelon' ? '#8fd86f' : '#ffd866'} opacity={0.9} />
      </g>
    </g>
  );
};
export type Prop = 'cash' | 'bread' | 'wrench' | 'fire' | 'clipboard' | 'magnifier' | 'cage' | 'cageQuiet' | 'pickaxe' | 'lunch' | undefined;
export type Fx = 'purple' | 'steam' | 'sweat' | 'sparkle' | 'alarm' | undefined;

const INK = '#1b1b24';
const SW = 6;

const TalkMouth = ({shape}: {shape: string}) => {
  const cx = 150, cy = 185;
  if (shape === 'A') return <line x1={cx - 16} y1={cy} x2={cx + 16} y2={cy} stroke={INK} strokeWidth={6} strokeLinecap="round" />;
  if (shape === 'E') return <ellipse cx={cx} cy={cy} rx={13} ry={15} fill="#4a1622" stroke={INK} strokeWidth={4} />;
  if (shape === 'F') return <ellipse cx={cx} cy={cy} rx={8} ry={9} fill="#4a1622" stroke={INK} strokeWidth={4} />;
  if (shape === 'G') return <path d={`M${cx - 18} ${cy - 4} Q${cx} ${cy + 14} ${cx + 18} ${cy - 4} Z`} fill="#4a1622" stroke={INK} strokeWidth={4} />;
  const ry = shape === 'B' ? 6 : shape === 'C' || shape === 'H' ? 12 : 19;
  return (
    <g>
      <ellipse cx={cx} cy={cy} rx={20} ry={ry} fill="#4a1622" stroke={INK} strokeWidth={4} />
      {ry > 8 && <ellipse cx={cx} cy={cy + ry * 0.5} rx={11} ry={ry * 0.35} fill="#ff6b81" />}
    </g>
  );
};

const Face = ({expr, t, talkShape}: {expr: Expr; t: number; talkShape?: string}) => {
  const L = 115, R = 185, EY = 128;
  const blink = Math.floor(t * 30) % 100 < 3;
  const dotEyes = (ry = 11) =>
    blink ? (
      <g>
        <line x1={L - 9} y1={EY} x2={L + 9} y2={EY} stroke={INK} strokeWidth={5} strokeLinecap="round" />
        <line x1={R - 9} y1={EY} x2={R + 9} y2={EY} stroke={INK} strokeWidth={5} strokeLinecap="round" />
      </g>
    ) : (
      <g fill={INK}>
        <ellipse cx={L} cy={EY} rx={7.5} ry={ry} />
        <ellipse cx={R} cy={EY} rx={7.5} ry={ry} />
      </g>
    );
  const arcEyes = (
    <g stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round">
      <path d={`M${L - 13} ${EY + 4} Q${L} ${EY - 12} ${L + 13} ${EY + 4}`} />
      <path d={`M${R - 13} ${EY + 4} Q${R} ${EY - 12} ${R + 13} ${EY + 4}`} />
    </g>
  );
  const brows = (lA: number, lB: number, rA: number, rB: number) => (
    <g stroke={INK} strokeWidth={7} strokeLinecap="round">
      <line x1={L - 18} y1={lA} x2={L + 14} y2={lB} />
      <line x1={R - 14} y1={rA} x2={R + 18} y2={rB} />
    </g>
  );
  let eyes: React.ReactNode, br: React.ReactNode = null, mouth: React.ReactNode, extra: React.ReactNode = null;
  switch (expr) {
    case 'smug':
      eyes = (
        <g>
          <path d={`M${L - 8} ${EY - 2} A8 11 0 0 0 ${L + 8} ${EY - 2} Z`} fill={INK} />
          <path d={`M${R - 8} ${EY - 2} A8 11 0 0 0 ${R + 8} ${EY - 2} Z`} fill={INK} />
          <line x1={L - 12} y1={EY - 2} x2={L + 12} y2={EY - 2} stroke={INK} strokeWidth={5} strokeLinecap="round" />
          <line x1={R - 12} y1={EY - 2} x2={R + 12} y2={EY - 2} stroke={INK} strokeWidth={5} strokeLinecap="round" />
        </g>
      );
      br = brows(100, 100, 92, 86);
      mouth = <path d="M128 182 Q160 196 178 172" stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
      break;
    case 'laugh':
      eyes = arcEyes;
      br = brows(96, 92, 92, 96);
      mouth = (
        <g>
          <path d="M118 170 Q150 225 182 170 Z" fill="#4a1622" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
          <ellipse cx={150} cy={198} rx={14} ry={7} fill="#ff6b81" />
        </g>
      );
      extra = (
        <g stroke={INK} strokeWidth={4} strokeLinecap="round">
          <line x1={238} y1={92} x2={256} y2={80} />
          <line x1={244} y1={112} x2={266} y2={108} />
        </g>
      );
      break;
    case 'shocked':
      eyes = (
        <g>
          <circle cx={L} cy={EY} r={19} fill="#fff" stroke={INK} strokeWidth={5} />
          <circle cx={R} cy={EY} r={19} fill="#fff" stroke={INK} strokeWidth={5} />
          <circle cx={L} cy={EY} r={6} fill={INK} />
          <circle cx={R} cy={EY} r={6} fill={INK} />
        </g>
      );
      br = brows(88, 82, 82, 88);
      mouth = <ellipse cx={150} cy={186} rx={13} ry={17} fill="#4a1622" stroke={INK} strokeWidth={5} />;
      break;
    case 'angry': {
      const flush = 0.25 + 0.15 * Math.sin(t * 8);
      extra = <circle cx={150} cy={130} r={92} fill="#c2185b" opacity={flush} />;
      eyes = dotEyes(9);
      br = brows(100, 114, 114, 100);
      mouth = (
        <g>
          <rect x={124} y={174} width={52} height={20} rx={5} fill="#fff" stroke={INK} strokeWidth={5} />
          <line x1={124} y1={184} x2={176} y2={184} stroke={INK} strokeWidth={3} />
          {[137, 150, 163].map((x) => <line key={x} x1={x} y1={174} x2={x} y2={194} stroke={INK} strokeWidth={3} />)}
        </g>
      );
      break;
    }
    case 'happy':
      eyes = arcEyes;
      br = brows(98, 94, 94, 98);
      mouth = <path d="M125 176 Q150 202 175 176" stroke={INK} strokeWidth={6} fill="none" strokeLinecap="round" />;
      break;
    case 'crazy':
      eyes = (
        <g>
          <circle cx={L} cy={EY} r={21} fill="#fff" stroke={INK} strokeWidth={5} />
          <circle cx={R} cy={EY} r={12} fill="#fff" stroke={INK} strokeWidth={5} />
          <circle cx={L + 4} cy={EY + 3} r={5} fill={INK} />
          <circle cx={R - 2} cy={EY} r={4} fill={INK} />
        </g>
      );
      br = brows(90, 84, 108, 104);
      mouth = (
        <g>
          <path d="M112 172 Q150 208 188 172 Z" fill="#fff" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
          {[127, 140, 153, 166, 177].map((x) => <line key={x} x1={x} y1={174} x2={x} y2={186} stroke={INK} strokeWidth={3} />)}
        </g>
      );
      break;
    case 'determined':
      eyes = dotEyes(9);
      br = brows(98, 108, 108, 98);
      mouth = <line x1={132} y1={184} x2={168} y2={182} stroke={INK} strokeWidth={6} strokeLinecap="round" />;
      break;
    case 'worried': {
      const drop = (t * 40) % 40;
      eyes = dotEyes(12);
      br = brows(104, 94, 94, 104);
      mouth = <path d="M128 186 Q139 178 150 186 Q161 194 172 186" stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" />;
      extra = <path d={`M232 ${78 + drop} q10 16 0 26 q-10 -10 0 -26 Z`} fill="#7fd3ff" stroke={INK} strokeWidth={3} />;
      break;
    }
    default:
      eyes = dotEyes();
      br = brows(100, 98, 98, 100);
      mouth = <line x1={136} y1={182} x2={164} y2={182} stroke={INK} strokeWidth={6} strokeLinecap="round" />;
  }
  const talking = talkShape && talkShape !== 'X';
  return (
    <g>
      {expr === 'angry' && extra}
      {eyes}
      {br}
      {talking ? <TalkMouth shape={talkShape} /> : mouth}
      {expr !== 'angry' && extra}
    </g>
  );
};

const Headwear = ({outfit}: {outfit: Outfit}) => {
  if (outfit === 'watermelon')
    return (
      <g>
        <path d="M150 38 Q148 16 160 6" stroke="#3e7a1f" strokeWidth={9} fill="none" strokeLinecap="round" />
        <path d="M160 8 q16 -10 24 4 q-12 10 -24 -4 Z" fill="#5fae2e" stroke={INK} strokeWidth={3} />
        <path d="M160 6 q10 6 4 14 q-6 6 0 12" stroke="#3e7a1f" strokeWidth={3} fill="none" />
      </g>
    );
  if (outfit === 'pineapple')
    return (
      <g>
        {/* spiky leaf crown */}
        {[[-48, -30], [-26, -48], [0, -60], [26, -48], [48, -30], [-12, -40], [14, -40]].map(([dx, h], n) => (
          <path key={n} d={`M${150 + dx * 0.5 - 12} 44 Q${150 + dx} ${44 + h * 0.6} ${150 + dx * 1.15} ${44 + h} Q${150 + dx * 0.7 + 8} ${44 + h * 0.5} ${150 + dx * 0.5 + 12} 44 Z`}
            fill={n % 2 ? '#2f9e44' : '#40c057'} stroke={INK} strokeWidth={4} strokeLinejoin="round" />
        ))}
        {/* tiny gold tiara */}
        <path d="M118 52 L124 30 L136 46 L150 24 L164 46 L176 30 L182 52 Z" fill="#ffd43b" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
        <circle cx={150} cy={40} r={5} fill="#e64980" />
        {/* lashes */}
        <g stroke={INK} strokeWidth={4} strokeLinecap="round">
          <line x1={100} y1={112} x2={94} y2={102} /><line x1={108} y1={108} x2={105} y2={97} />
          <line x1={200} y1={112} x2={206} y2={102} /><line x1={192} y1={108} x2={195} y2={97} />
        </g>
      </g>
    );
  if (outfit === 'miner' || outfit === 'digger') {
    const hat = outfit === 'miner' ? '#f2b705' : '#8a6a44';
    return (
      <g>
        {outfit === 'digger' && (
          /* bushy black beard */
          <path d="M66 150 Q70 232 150 238 Q230 232 234 150 Q214 196 190 186 Q150 204 110 186 Q86 196 66 150 Z" fill="#2b2420" stroke={INK} strokeWidth={4} />
        )}
        {/* hard hat with brim */}
        <path d="M60 104 Q60 22 150 20 Q240 22 240 104 Z" fill={hat} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M150 22 L150 102" stroke={INK} strokeWidth={4} opacity={0.35} />
        <rect x={42} y={94} width={216} height={20} rx={10} fill={hat} stroke={INK} strokeWidth={SW} />
        {outfit === 'miner' && (
          <g>
            {/* headlamp */}
            <rect x={128} y={44} width={44} height={34} rx={8} fill="#5c5f6b" stroke={INK} strokeWidth={5} />
            <circle cx={150} cy={61} r={11} fill="#fff6c4" stroke={INK} strokeWidth={3} />
            {/* soot smudges */}
            <ellipse cx={92} cy={170} rx={14} ry={7} fill="#3a3a44" opacity={0.35} />
            <ellipse cx={212} cy={120} rx={10} ry={6} fill="#3a3a44" opacity={0.3} />
          </g>
        )}
      </g>
    );
  }
  if (outfit === 'engineer')
    return (
      <g>
        {/* messy red hair */}
        <path d="M62 112 L52 70 L82 84 L80 40 L112 66 L124 22 L148 58 L172 18 L184 60 L214 30 L214 74 L246 62 L238 112 Q228 76 190 70 Q150 86 108 70 Q74 80 62 112 Z"
          fill="#d9531e" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        {/* big round glasses */}
        <g fill="rgba(200,230,255,.25)" stroke={INK} strokeWidth={6}>
          <circle cx={115} cy={128} r={27} />
          <circle cx={185} cy={128} r={27} />
        </g>
        <line x1={142} y1={126} x2={158} y2={126} stroke={INK} strokeWidth={6} />
      </g>
    );
  if (outfit === 'boss')
    return (
      <g>
        {/* bald with grey side tufts + shine */}
        <path d="M58 150 Q50 110 70 92 Q78 120 72 150 Z" fill="#b8bcc6" stroke={INK} strokeWidth={5} />
        <path d="M242 150 Q250 110 230 92 Q222 120 228 150 Z" fill="#b8bcc6" stroke={INK} strokeWidth={5} />
        <ellipse cx={120} cy={62} rx={22} ry={10} fill="#fff" opacity={0.9} transform="rotate(-25 120 62)" />
        {/* big walrus moustache */}
        <path d="M150 162 Q118 140 88 172 Q96 186 112 176 Q130 172 150 176 Q170 172 188 176 Q204 186 212 172 Q182 140 150 162 Z"
          fill="#9aa0ab" stroke={INK} strokeWidth={4} />
      </g>
    );
  if (outfit === 'leo')
    return (
      <g>
        <path d="M58 118 Q60 30 150 30 Q246 32 242 118 Q232 70 190 62 Q150 82 100 66 Q70 80 58 118 Z" fill="#20202c" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M110 66 Q150 46 196 62" stroke="#4a4a60" strokeWidth={5} fill="none" />
      </g>
    );
  if (outfit === 'baker')
    return (
      <g>
        <rect x={92} y={42} width={116} height={40} rx={6} fill="#fff" stroke={INK} strokeWidth={SW} />
        <path d="M88 50 Q70 10 108 4 Q120 -22 150 -10 Q182 -26 194 6 Q232 8 212 50 Z" fill="#fff" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        {/* moustache */}
        <path d="M150 166 Q128 150 108 168 Q128 162 150 172 Q172 162 192 168 Q172 150 150 166 Z" fill="#6b4226" stroke={INK} strokeWidth={3} />
      </g>
    );
  return (
    <g>
      <path d="M56 112 Q58 24 150 22 Q242 24 244 112 Z" fill="#ff7b29" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
      <rect x={52} y={96} width={196} height={26} rx={12} fill="#e0611a" stroke={INK} strokeWidth={SW} />
      <circle cx={150} cy={20} r={14} fill="#ffb347" stroke={INK} strokeWidth={5} />
    </g>
  );
};

const Torso = ({outfit}: {outfit: Outfit}) => {
  const base = 'M95 232 Q150 218 205 232 L218 400 Q150 414 82 400 Z';
  if (outfit === 'watermelon')
    return (
      <g>
        <path d={base} fill="#ff4d6d" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M84 384 Q150 398 216 384 L218 400 Q150 414 82 400 Z" fill="#2e7d32" />
        {[[120, 270], [175, 285], [140, 320], [190, 340], [112, 355], [160, 365]].map(([x, y], n) => (
          <ellipse key={n} cx={x} cy={y} rx={5} ry={8} fill={INK} transform={`rotate(${n * 25} ${x} ${y})`} />
        ))}
      </g>
    );
  if (outfit === 'pineapple')
    return (
      <g>
        <path d="M100 232 Q150 218 200 232 L236 404 Q150 420 64 404 Z" fill="#ff922b" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M108 290 Q150 302 192 290" stroke="#2f9e44" strokeWidth={12} fill="none" />
        <circle cx={150} cy={296} r={9} fill="#e64980" stroke={INK} strokeWidth={3} />
      </g>
    );
  if (outfit === 'engineer')
    return (
      <g>
        <path d={base} fill="#f7f7f2" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M128 228 L150 330 L172 228 Z" fill="#5b8fd6" stroke={INK} strokeWidth={4} />
        <line x1={150} y1={330} x2={150} y2={404} stroke={INK} strokeWidth={4} />
        <rect x={168} y={262} width={26} height={30} rx={3} fill="none" stroke={INK} strokeWidth={3} />
        <line x1={174} y1={250} x2={174} y2={270} stroke="#e63946" strokeWidth={5} strokeLinecap="round" />
        <line x1={184} y1={250} x2={184} y2={270} stroke="#1d3557" strokeWidth={5} strokeLinecap="round" />
      </g>
    );
  if (outfit === 'miner' || outfit === 'digger')
    return (
      <g>
        <path d={base} fill={outfit === 'miner' ? '#c4583a' : '#6d7a5a'} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        {/* denim overalls */}
        <path d="M108 290 L192 290 L214 400 Q150 412 86 400 Z" fill="#3b5f8a" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
        <line x1={114} y1={232} x2={118} y2={292} stroke="#3b5f8a" strokeWidth={12} />
        <line x1={186} y1={232} x2={182} y2={292} stroke="#3b5f8a" strokeWidth={12} />
        <circle cx={118} cy={296} r={6} fill="#f2b705" stroke={INK} strokeWidth={2} />
        <circle cx={182} cy={296} r={6} fill="#f2b705" stroke={INK} strokeWidth={2} />
        <rect x={132} y={318} width={36} height={26} rx={4} fill="none" stroke={INK} strokeWidth={3} />
        {outfit === 'miner' && <path d="M112 230 Q150 252 188 230 L184 246 Q150 266 116 246 Z" fill="#e63946" stroke={INK} strokeWidth={3} />}
        <ellipse cx={176} cy={372} rx={16} ry={8} fill="#1b1b24" opacity={0.25} />
      </g>
    );
  if (outfit === 'boss')
    return (
      <g>
        <path d={base} fill="#1f2d4d" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M128 228 L150 290 L172 228 Z" fill="#fff" stroke={INK} strokeWidth={4} />
        <path d="M130 234 L150 244 L170 234 L170 256 L150 246 L130 256 Z" fill="#d62828" stroke={INK} strokeWidth={3} />
        {[300, 340, 380].map((y) => <circle key={y} cx={150} cy={y} r={6} fill="#f2b705" stroke={INK} strokeWidth={2} />)}
      </g>
    );
  if (outfit === 'leo')
    return (
      <g>
        <path d={base} fill="#6b3fa0" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M128 228 L150 290 L172 228 Z" fill="#fff" stroke={INK} strokeWidth={4} />
        <path d="M144 240 L156 240 L160 300 L150 312 L140 300 Z" fill="#f2b705" stroke={INK} strokeWidth={4} />
        <path d="M100 330 Q150 360 200 330" stroke="#f2b705" strokeWidth={5} fill="none" strokeDasharray="8 6" />
      </g>
    );
  if (outfit === 'baker')
    return (
      <g>
        <path d={base} fill="#f3f3f3" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        <path d="M112 270 L188 270 L196 402 Q150 410 104 402 Z" fill="#fff" stroke={INK} strokeWidth={4} />
        <rect x={130} y={320} width={40} height={30} rx={4} fill="none" stroke={INK} strokeWidth={4} />
      </g>
    );
  return (
    <g>
      <path d={base} fill="#8d99ae" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
      <path d="M100 300 L200 300 L216 400 Q150 412 84 400 Z" fill="#2f6fb5" stroke={INK} strokeWidth={5} />
      <line x1={110} y1={232} x2={115} y2={300} stroke="#2f6fb5" strokeWidth={10} />
      <line x1={190} y1={232} x2={185} y2={300} stroke="#2f6fb5" strokeWidth={10} />
      <circle cx={116} cy={304} r={5} fill="#f2b705" />
      <circle cx={184} cy={304} r={5} fill="#f2b705" />
    </g>
  );
};

const PropView = ({prop, t}: {prop: Prop; t: number}) => {
  if (!prop) return null;
  const hx = 252, hy = 372;
  if (prop === 'cash' || prop === 'fire')
    return (
      <g>
        {[0, 1, 2, 3].map((i) => (
          <rect key={i} x={hx - 34} y={hy - 12 - i * 9} width={68} height={30} rx={3} fill="#4caf50" stroke="#1d5e20" strokeWidth={3} />
        ))}
        <rect x={hx - 8} y={hy - 39} width={16} height={30} fill="#f2b705" opacity={0.85} />
        {prop === 'fire' &&
          [0, 1, 2].map((i) => {
            const fl = Math.sin(t * 18 + i * 2) * 6;
            const h = 120 + Math.sin(t * 11 + i) * 22;
            const x = hx - 26 + i * 26;
            return (
              <path key={i} d={`M${x - 16} ${hy - 36} Q${x - 20 + fl} ${hy - 36 - h * 0.6} ${x + fl} ${hy - 36 - h} Q${x + 20 + fl} ${hy - 36 - h * 0.6} ${x + 16} ${hy - 36} Z`}
                fill={i === 1 ? '#ffd23f' : '#ff6b1a'} stroke="#b33a00" strokeWidth={3} opacity={0.95} />
            );
          })}
      </g>
    );
  if (prop === 'cage' || prop === 'cageQuiet') {
    const sing = prop === 'cage';
    const bob = sing ? Math.abs(Math.sin(t * 9)) * 6 : 0;
    const cx = hx + 14, top = hy - 6;
    return (
      <g transform={`translate(${hx} ${hy}) scale(1.35) translate(${-hx} ${-hy})`}>
        {/* hook + ring */}
        <circle cx={cx} cy={top} r={9} fill="none" stroke="#8a6d1f" strokeWidth={5} />
        {/* bird */}
        <g transform={`translate(${cx} ${top + 84 - bob}) rotate(${sing ? Math.sin(t * 9) * 8 : 0})`}>
          <path d="M-22 10 L-40 22 L-26 4 Z" fill="#e0a800" stroke={INK} strokeWidth={3} />
          <ellipse cx={0} cy={6} rx={24} ry={18} fill="#ffd23f" stroke={INK} strokeWidth={4} />
          <circle cx={16} cy={-14} r={14} fill="#ffd23f" stroke={INK} strokeWidth={4} />
          <path d={sing ? 'M28 -18 L44 -22 L30 -10 L44 -4 L28 -8 Z' : 'M28 -16 L42 -12 L28 -8 Z'} fill="#ff8c1a" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
          {sing ? <circle cx={20} cy={-17} r={3.5} fill={INK} /> : <path d="M15 -16 L25 -16" stroke={INK} strokeWidth={3.5} strokeLinecap="round" />}
          <path d="M-8 4 Q2 16 12 4" stroke="#e0a800" strokeWidth={4} fill="none" />
        </g>
        {/* perch */}
        <line x1={cx - 34} y1={top + 106} x2={cx + 34} y2={top + 106} stroke="#8a6d1f" strokeWidth={5} />
        {/* cage bars */}
        <path d={`M${cx - 50} ${top + 128} L${cx - 50} ${top + 52} Q${cx} ${top - 4} ${cx + 50} ${top + 52} L${cx + 50} ${top + 128}`} fill="none" stroke="#c9a227" strokeWidth={6} />
        {[-30, -10, 10, 30].map((dx) => (
          <path key={dx} d={`M${cx + dx} ${top + 128} L${cx + dx} ${top + 46 + Math.abs(dx) * 0.4} Q${cx + dx * 0.5} ${top + 14} ${cx} ${top + 8}`} fill="none" stroke="#c9a227" strokeWidth={4} />
        ))}
        <rect x={cx - 58} y={top + 124} width={116} height={14} rx={4} fill="#8a6d1f" stroke={INK} strokeWidth={4} />
        {/* song notes */}
        {sing && [0, 1, 2].map((n) => {
          const ph = (t * 0.9 + n / 3) % 1;
          return (
            <g key={n} transform={`translate(${cx + 40 + ph * 50 + Math.sin(ph * 9) * 10} ${top + 40 - ph * 130}) scale(${0.7 + ph * 0.5})`} opacity={1 - ph}>
              <path d="M0 0 L0 -26 L14 -30 L14 -6" stroke={INK} strokeWidth={4} fill="none" />
              <ellipse cx={-5} cy={2} rx={7} ry={5} fill={INK} />
              <ellipse cx={9} cy={-2} rx={7} ry={5} fill={INK} />
            </g>
          );
        })}
      </g>
    );
  }
  if (prop === 'pickaxe')
    return (
      <g transform={`translate(${hx} ${hy}) rotate(-30)`}>
        <rect x={-6} y={-120} width={12} height={150} rx={5} fill="#8a5a2b" stroke={INK} strokeWidth={4} />
        <path d="M-70 -110 Q0 -150 70 -110 Q0 -128 -70 -110 Z" fill="#9aa5b1" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
      </g>
    );
  if (prop === 'lunch')
    return (
      <g transform={`translate(${hx - 30} ${hy - 30})`}>
        <rect x={0} y={0} width={70} height={44} rx={6} fill="#7a8794" stroke={INK} strokeWidth={4} />
        <path d="M14 0 Q35 -26 56 0" stroke={INK} strokeWidth={4} fill="none" />
        <path d="M18 -6 Q30 -20 46 -10 Q42 0 18 -6 Z" fill="#e8b96a" stroke={INK} strokeWidth={3} />
      </g>
    );
  if (prop === 'clipboard')
    return (
      <g transform={`translate(${hx - 30} ${hy - 70}) rotate(8)`}>
        <rect x={0} y={0} width={64} height={84} rx={5} fill="#a0703a" stroke={INK} strokeWidth={4} />
        <rect x={7} y={12} width={50} height={64} fill="#fff" />
        <rect x={20} y={-6} width={24} height={14} rx={3} fill="#9aa5b1" stroke={INK} strokeWidth={3} />
        {[26, 38, 50, 62].map((y) => <line key={y} x1={13} y1={y} x2={51} y2={y} stroke="#9aa5b1" strokeWidth={3} />)}
      </g>
    );
  if (prop === 'magnifier')
    return (
      <g>
        <line x1={hx} y1={hy} x2={hx - 18} y2={hy - 48} stroke="#6b4226" strokeWidth={12} strokeLinecap="round" />
        <circle cx={hx - 30} cy={hy - 82} r={36} fill="rgba(190,230,255,.35)" stroke={INK} strokeWidth={8} />
        <path d={`M${hx - 48} ${hy - 96} Q${hx - 40} ${hy - 108} ${hx - 26} ${hy - 108}`} stroke="#fff" strokeWidth={5} fill="none" />
      </g>
    );
  if (prop === 'bread')
    return (
      <g>
        {[0, 1, 2].map((i) => (
          <g key={i} transform={`translate(${hx - 10} ${hy - 20 - i * 26}) rotate(-12)`}>
            <ellipse cx={0} cy={0} rx={44} ry={17} fill="#d9963f" stroke="#6b4226" strokeWidth={4} />
            {[-18, 0, 18].map((x) => <line key={x} x1={x - 5} y1={-8} x2={x + 5} y2={6} stroke="#8a5a2b" strokeWidth={3} />)}
          </g>
        ))}
      </g>
    );
  return (
    <g transform={`translate(${hx} ${hy}) rotate(-35)`}>
      <rect x={-7} y={-80} width={14} height={90} rx={5} fill="#9aa5b1" stroke={INK} strokeWidth={4} />
      <path d="M-22 -96 Q0 -120 22 -96 L12 -80 L-12 -80 Z" fill="#9aa5b1" stroke={INK} strokeWidth={4} />
    </g>
  );
};

export type Pose = 'idle' | 'reach' | 'give' | 'point' | 'slam' | 'handsUp' | 'wave' | 'knock' | 'fist' | 'crouch' | 'hip' | 'shout';

/** Comic effects drawn on/around the head. ft = seconds since the effect started. */
const HeadFx = ({fx, ft, t}: {fx: Fx; ft: number; t: number}) => {
  if (fx === 'steam')
    return (
      <g>
        {[-1, 1].map((side) => {
          const puff = 0.8 + 0.35 * Math.abs(Math.sin(t * 7 + side));
          const rise = (t * 60) % 30;
          const cx = 150 + side * 108, cy = 36 - rise;
          return (
            <g key={side} transform={`translate(${cx} ${cy}) scale(${puff})`} opacity={0.95}>
              {[[-18, 6, 18], [0, -8, 22], [18, 6, 18], [0, 12, 16]].map(([x, y, r], n) => (
                <circle key={n} cx={x} cy={y} r={r} fill="#fff" stroke="#9aa0ab" strokeWidth={3} />
              ))}
            </g>
          );
        })}
      </g>
    );
  if (fx === 'sweat')
    return (
      <g>
        {[0, 1].map((n) => {
          const d = ((t + n * 0.45) * 50) % 45;
          return <path key={n} d={`M${236 - n * 160} ${84 + d} q11 18 0 28 q-11 -10 0 -28 Z`} fill="#7fd3ff" stroke={INK} strokeWidth={3} opacity={1 - d / 45} />;
        })}
      </g>
    );
  if (fx === 'sparkle')
    return (
      <g fill="#ffd23f" stroke={INK} strokeWidth={3}>
        {[[40, 40], [262, 60], [250, -10], [52, -20]].map(([x, y], n) => {
          const s = 0.5 + 0.5 * Math.abs(Math.sin(t * 6 + n * 1.7));
          return <path key={n} transform={`translate(${x} ${y}) scale(${s})`} d="M0 -22 L6 -6 L22 0 L6 6 L0 22 L-6 6 L-22 0 L-6 -6 Z" />;
        })}
      </g>
    );
  if (fx === 'alarm') {
    const pop = Math.min(1, ft / 0.15);
    return (
      <g transform={`translate(150 -30) scale(${pop})`} stroke={INK} strokeWidth={6} strokeLinecap="round">
        <line x1={-70} y1={10} x2={-95} y2={-20} />
        <line x1={0} y1={-10} x2={0} y2={-48} />
        <line x1={70} y1={10} x2={95} y2={-20} />
      </g>
    );
  }
  return null;
};

type P = [number, number];

/** Hand positions (in character space) for a pose. pt = seconds since the pose started. */
const handsFor = (pose: Pose, pt: number, t: number, walk: number | null, hasProp: boolean): {L: P; R: P} => {
  const sw = walk !== null ? Math.sin(walk) * 24 : Math.sin(t * 2.5) * 5;
  let L: P = walk !== null ? [60 - sw, 368] : [52, 372 + sw];
  let R: P = walk !== null ? [240 + sw, 368] : [248, 372 - sw];
  if (hasProp) R = [252, 372];
  switch (pose) {
    case 'reach': R = [305, 300]; break;
    case 'give': R = [305, 318]; break;
    case 'point': R = [282, 178]; break;
    case 'slam': {
      const k = Math.min(1, pt / 0.16);
      R = [272, 170 + k * 225];
      break;
    }
    case 'handsUp': L = [28, 168 + Math.sin(t * 20) * 6]; R = [272, 168 - Math.sin(t * 20) * 6]; break;
    case 'wave': R = [268 + Math.sin(pt * 14) * 20, 165]; break;
    case 'knock': R = [306 - Math.abs(Math.sin((pt * Math.PI) / 0.3)) * 24, 292]; break;
    case 'fist': L = [62, 318 + Math.sin(t * 22) * 7]; R = [238, 318 - Math.sin(t * 22) * 7]; break;
    case 'crouch': L = [70, 360]; R = hasProp ? [228, 262] : [240, 330]; break;
    case 'hip': L = [92, 338]; break;
    case 'shout': L = [36, 186 + Math.sin(t * 24) * 8]; R = [264, 186 - Math.sin(t * 24) * 8]; break;
  }
  return {L, R};
};

const Arm = ({from, to, side}: {from: P; to: P; side: -1 | 1}) => {
  const mx = (from[0] + to[0]) / 2 + side * 22;
  const my = (from[1] + to[1]) / 2 + 10;
  return (
    <g>
      <path d={`M${from[0]} ${from[1]} Q${mx} ${my} ${to[0]} ${to[1]}`} stroke={INK} strokeWidth={9} strokeLinecap="round" fill="none" />
      <circle cx={to[0]} cy={to[1] + 4} r={13} fill="#fff" stroke={INK} strokeWidth={5} />
    </g>
  );
};

export const Character: React.FC<{
  outfit: Outfit; expr: Expr; t: number; talkShape?: string; prop?: Prop; flip?: boolean;
  pose?: Pose; poseT?: number; walk?: number | null; fx?: Fx; fxT?: number;
}> = ({outfit, expr, t, talkShape, prop, flip, pose = 'idle', poseT = 0, walk = null, fx, fxT = 0}) => {
  const talking = talkShape && talkShape !== 'X';
  const walking = walk !== null;
  const crouch = pose === 'crouch' ? 80 : 0;
  const bob = crouch + (walking ? -Math.abs(Math.sin(walk)) * 8 : Math.sin(t * 3 + outfit.length) * 4);
  // purple rage fill rises from the chin; steam implies a full face
  const purple = fx === 'purple' ? Math.min(1, fxT / 0.9) : fx === 'steam' ? 1 : 0;
  const headBob = talking ? Math.sin(t * 14) * 3 : 0;
  const shake = expr === 'angry' ? Math.sin(t * 40) * 2 : 0;
  const lean = walking ? 4 : pose === 'slam' ? 6 : 0;
  const {L, R} = handsFor(pose, poseT, t, walk, !!prop);
  // legs: feet swing and lift while walking
  const s = walking ? Math.sin(walk) : 0;
  const c = walking ? Math.cos(walk) : 0;
  const fL: P = [118 + s * 32, 565 - Math.max(0, c) * 18];
  const fR: P = [182 - s * 32, 565 - Math.max(0, -c) * 18];
  return (
    <svg viewBox="-20 -40 340 640" width="100%" height="100%" style={{overflow: 'visible', transform: flip ? 'scaleX(-1)' : undefined}}>
      <ellipse cx={150} cy={578} rx={80} ry={12} fill="#000" opacity={0.3} />
      <g stroke={INK} strokeWidth={9} strokeLinecap="round" fill="none">
        {crouch ? (
          <>
            <polyline points={`125,${400 + bob} 78,${500} ${fL[0]},${fL[1]}`} strokeLinejoin="round" />
            <polyline points={`175,${400 + bob} 222,${500} ${fR[0]},${fR[1]}`} strokeLinejoin="round" />
          </>
        ) : (
          <>
            <line x1={125} y1={400 + bob} x2={fL[0]} y2={fL[1]} />
            <line x1={175} y1={400 + bob} x2={fR[0]} y2={fR[1]} />
          </>
        )}
      </g>
      <ellipse cx={fL[0] - 8} cy={fL[1] + 3} rx={20} ry={9} fill={INK} />
      <ellipse cx={fR[0] + 8} cy={fR[1] + 3} rx={20} ry={9} fill={INK} />
      <g transform={`translate(${shake} ${bob}) rotate(${lean} 150 400)`}>
        <Arm from={[96, 248]} to={L} side={-1} />
        <Torso outfit={outfit} />
        <g transform={`translate(${R[0] - 252} ${R[1] - 372})`}>
          <PropView prop={prop} t={t} />
        </g>
        <Arm from={[204, 248]} to={R} side={1} />
        <g transform={`translate(0 ${headBob})`}>
          <circle cx={150} cy={130} r={95} fill={HEAD_FILL[outfit] ?? '#fff'} stroke={INK} strokeWidth={SW} />
          <HeadSkin outfit={outfit} />
          {purple > 0 && (
            <g>
              <clipPath id={`head-${outfit}`}><circle cx={150} cy={130} r={92} /></clipPath>
              <g clipPath={`url(#head-${outfit})`}>
                <rect x={50} y={226 - 196 * purple} width={200} height={200} fill="#8e44ad" />
                <path d={`M50 ${226 - 196 * purple} q25 ${-8 + Math.sin(t * 9) * 5} 50 0 t50 0 t50 0 t50 0`} fill="#8e44ad" />
              </g>
            </g>
          )}
          <Face expr={expr} t={t} talkShape={talkShape} />
          <Headwear outfit={outfit} />
          <HeadFx fx={fx} ft={fxT} t={t} />
        </g>
      </g>
    </svg>
  );
};
