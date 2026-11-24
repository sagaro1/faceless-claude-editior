import {Composition} from 'remotion';
import {makeShort} from './Engine';
import exampleTimeline from '../public/example/timeline.json';
import exampleBoard from '../public/example/storyboard.json';

export const FPS = 30;
const vertical = {fps: FPS, width: 1080, height: 1920};

// Example short: examples/example.txt -> dialogue_voice.py -> public/example/{timeline.json, voice.mp3}
const example = makeShort(exampleTimeline, exampleBoard, 'example', {captionY: 1350, music: 0.1});

// Private compositions live in ./client (git-ignored). Loaded only if present, so forks still build.
const clientCtx = (require as any).context('./client', false, /Root\.tsx$/);
const ClientComps = () => (
  <>{clientCtx.keys().map((k: string) => { const C = clientCtx(k).ClientCompositions; return C ? <C key={k} /> : null; })}</>
);

export const RemotionRoot = () => (
  <>
    <Composition id="ExampleShort" component={example.Comp} durationInFrames={Math.ceil((example.END + 1.2) * FPS)} {...vertical} />
    <ClientComps />
  </>
);
