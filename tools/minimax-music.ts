import Replicate from 'replicate';
import { config } from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import ora from 'ora';
import chalk from 'chalk';
import * as path from 'path';
import * as fs from 'fs';
import { downloadFile } from './utils/download';

config({
  path: process.env.NODE_ENV === 'development' ? '.env.local' : '.env',
});

const MUSIC_MODEL = 'minimax/music-2.6' as const;

const SAMPLE_RATES = [16000, 24000, 32000, 44100] as const;
const BITRATES = [32000, 64000, 128000, 256000] as const;
const AUDIO_FORMATS = ['mp3', 'wav', 'pcm'] as const;

const MAX_PROMPT_CHARS = 2000;
const MAX_LYRICS_CHARS = 3500;

type SampleRate = (typeof SAMPLE_RATES)[number];
type Bitrate = (typeof BITRATES)[number];
type AudioFormat = (typeof AUDIO_FORMATS)[number];

export interface MinimaxMusicOptions {
  prompt: string;
  lyrics?: string;
  instrumental?: boolean;
  lyricsOptimizer?: boolean;
  sampleRate?: SampleRate;
  bitrate?: Bitrate;
  audioFormat?: AudioFormat;
  seed?: number;
  output?: string;
  folder?: string;
}

function extractAudioUrl(output: unknown): string | undefined {
  if (typeof output === 'string') {
    return output;
  }
  // Replicate client may return FileOutput (ReadableStream with url() / toString())
  if (
    output != null &&
    typeof output === 'object' &&
    'url' in output &&
    typeof (output as { url: unknown }).url === 'function'
  ) {
    const href = (output as { url: () => URL }).url().href;
    if (href.startsWith('http')) return href;
  }
  if (Array.isArray(output)) {
    const fromArray = output.find(
      (u) => typeof u === 'string' && (u.includes('http') || u.includes('replicate')),
    );
    if (fromArray) return fromArray;
    if (output.length > 0 && typeof output[0] === 'string') {
      return output[0];
    }
  }
  if (output && typeof output === 'object') {
    const obj = output as Record<string, unknown>;
    const candidates = ['output', 'audio', 'audio_url', 'url', 'file', 'result'];
    for (const key of candidates) {
      const val = obj[key];
      if (typeof val === 'string' && val.length > 0) {
        return val;
      }
      if (Array.isArray(val) && val.length > 0) {
        const first = val.find((v: unknown) => typeof v === 'string');
        if (first) return first as string;
      }
    }
  }
  return undefined;
}

function extForFormat(format: AudioFormat): string {
  if (format === 'pcm') return '.pcm';
  if (format === 'wav') return '.wav';
  return '.mp3';
}

export async function generateMusic(options: MinimaxMusicOptions): Promise<string> {
  const spinner = ora('Initializing MiniMax Music 2.6...').start();

  try {
    if (!process.env.REPLICATE_API_TOKEN) {
      throw new Error('REPLICATE_API_TOKEN is required in .env.local');
    }

    const { prompt, lyrics, instrumental, lyricsOptimizer } = options;

    if (instrumental) {
      if (lyrics && lyrics.trim().length > 0) {
        throw new Error('Instrumental mode does not use lyrics; omit --lyrics / --lyrics-file');
      }
    } else if (lyricsOptimizer) {
      if (lyrics && lyrics.trim().length > 0) {
        throw new Error('Use either --lyrics-optimizer or lyrics, not both');
      }
    } else {
      if (!lyrics || lyrics.trim().length === 0) {
        throw new Error('Provide --lyrics or --lyrics-file, or use --lyrics-optimizer or --instrumental');
      }
    }

    if (prompt.length > MAX_PROMPT_CHARS) {
      throw new Error(`Prompt exceeds ${MAX_PROMPT_CHARS} characters`);
    }
    if (lyrics && lyrics.length > MAX_LYRICS_CHARS) {
      throw new Error(`Lyrics exceed ${MAX_LYRICS_CHARS} characters`);
    }
    if (options.seed !== undefined && (options.seed < 0 || options.seed > 1_000_000)) {
      throw new Error('Seed must be between 0 and 1000000');
    }

    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
      // Plain https URLs (FileOutput streams break our downloader)
      useFileOutput: false,
    });

    const input: Record<string, string | number | boolean> = {
      prompt,
      is_instrumental: !!instrumental,
      lyrics_optimizer: !!lyricsOptimizer && !instrumental,
    };

    if (lyrics && lyrics.trim().length > 0 && !instrumental && !lyricsOptimizer) {
      input.lyrics = lyrics;
    }

    if (options.sampleRate !== undefined) {
      input.sample_rate = options.sampleRate;
    }
    if (options.bitrate !== undefined) {
      input.bitrate = options.bitrate;
    }
    if (options.audioFormat !== undefined) {
      input.audio_format = options.audioFormat;
    }
    if (options.seed !== undefined) {
      input.seed = options.seed;
    }

    spinner.text = 'Generating music (this may take a few minutes)...';
    const output = await replicate.run(MUSIC_MODEL, { input });

    const audioUrl = extractAudioUrl(output);
    if (!audioUrl) {
      throw new Error('Could not read audio URL from model output');
    }

    const format = options.audioFormat ?? 'mp3';
    const outputFolder = options.folder ?? 'public/audio';
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder, { recursive: true });
    }

    const defaultName = `minimax-music-${Date.now()}${extForFormat(format)}`;
    const filename = options.output ?? defaultName;
    const outputPath = path.join(outputFolder, filename);

    spinner.text = 'Downloading audio...';
    await downloadFile(audioUrl, outputPath);

    spinner.succeed(chalk.green(`Music saved: ${outputPath}`));
    console.log(chalk.cyan('\nMusic generation summary'));
    console.log(chalk.gray('  Prompt:'), prompt.slice(0, 80) + (prompt.length > 80 ? '…' : ''));
    console.log(chalk.gray('  Mode:'), instrumental ? 'instrumental' : lyricsOptimizer ? 'auto lyrics' : 'lyrics + style');
    console.log(chalk.gray('  Output:'), outputPath);

    return outputPath;
  } catch (error: unknown) {
    spinner.fail(
      chalk.red(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`),
    );
    throw error;
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage('Usage: $0 [options]')
    .option('prompt', {
      alias: 'p',
      type: 'string',
      description: 'Style / direction: key, BPM, genre, mood, vocals, instruments (see MiniMax Music 2.6 docs)',
      demandOption: true,
    })
    .option('lyrics', {
      alias: 'l',
      type: 'string',
      description: 'Song lyrics (use section tags like [Verse], [Chorus]); not used with --instrumental',
    })
    .option('lyrics-file', {
      type: 'string',
      description: 'Path to a text file with lyrics (UTF-8)',
    })
    .option('instrumental', {
      alias: 'i',
      type: 'boolean',
      description: 'Instrumental only; prompt describes the music',
      default: false,
    })
    .option('lyrics-optimizer', {
      type: 'boolean',
      description: 'Let the model write lyrics from the prompt (no --lyrics)',
      default: false,
    })
    .option('sample-rate', {
      type: 'number',
      choices: [...SAMPLE_RATES] as unknown as number[],
      description: 'Audio sample rate (default on API: 44100)',
    })
    .option('bitrate', {
      type: 'number',
      choices: [...BITRATES] as unknown as number[],
      description: 'Bitrate (default on API: 256000)',
    })
    .option('audio-format', {
      type: 'string',
      choices: [...AUDIO_FORMATS] as unknown as string[],
      description: 'Output format',
      default: 'mp3',
    })
    .option('seed', {
      type: 'number',
      description: 'Reproducibility seed (0–1000000)',
    })
    .option('output', {
      alias: 'o',
      type: 'string',
      description: 'Output filename (default: minimax-music-<timestamp>.<ext>)',
    })
    .option('folder', {
      alias: 'f',
      type: 'string',
      description: 'Output directory',
      default: 'public/audio',
    })
    .check((a) => {
      if (a['lyrics-file'] && a.lyrics) {
        throw new Error('Use either --lyrics or --lyrics-file, not both');
      }
      return true;
    })
    .example([
      [
        '$0 -p "E minor, 90 BPM, acoustic ballad, male vocal, emotional" -l "[Verse]\\nHello world"',
        'Song with lyrics',
      ],
      ['$0 -p "Cinematic orchestral, epic, 90 BPM" -i', 'Instrumental'],
      ['$0 -p "Upbeat summer pop, catchy" --lyrics-optimizer', 'Auto-generated lyrics'],
    ])
    .help()
    .alias('help', 'h')
    .argv;

  let lyrics = argv.lyrics;
  if (argv['lyrics-file']) {
    const fp = argv['lyrics-file'];
    if (!fs.existsSync(fp)) {
      console.error(chalk.red(`Lyrics file not found: ${fp}`));
      process.exit(1);
    }
    lyrics = fs.readFileSync(fp, 'utf-8');
  }

  try {
    await generateMusic({
      prompt: argv.prompt,
      lyrics,
      instrumental: argv.instrumental,
      lyricsOptimizer: argv['lyrics-optimizer'],
      sampleRate: argv['sample-rate'] as SampleRate | undefined,
      bitrate: argv.bitrate as Bitrate | undefined,
      audioFormat: argv['audio-format'] as AudioFormat,
      seed: argv.seed,
      output: argv.output,
      folder: argv.folder,
    });
  } catch {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
