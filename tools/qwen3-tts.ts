import Replicate from 'replicate';
import { config } from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import ora from 'ora';
import chalk from 'chalk';
import * as path from 'path';
import * as fs from 'fs';
import { downloadFile } from './utils/download';

// Load environment variables
config({
  path: process.env.NODE_ENV === 'development' ? '.env.local' : '.env'
});

// Qwen3-TTS model identifier on Replicate
const QWEN3_TTS_MODEL = 'qwen/qwen3-tts';

// Supported modes (user-friendly names mapped to API values)
type TTSMode = 'voice' | 'clone' | 'design';

// API mode mapping
const API_MODES: Record<TTSMode, string> = {
  'voice': 'custom_voice',
  'clone': 'voice_clone',
  'design': 'voice_design',
};

interface TTSOptions {
  text: string;
  mode: TTSMode;
  output?: string;
  folder?: string;
  // Voice mode options
  voicePrompt?: string;
  // Clone mode options
  refAudio?: string;
  refText?: string;
  // Design mode options
  voiceDescription?: string;
}

/**
 * Convert a local file to a base64 data URI
 */
function fileToDataUri(filePath: string, mimeType: string = 'audio/wav'): string {
  const buffer = fs.readFileSync(filePath);
  const base64 = buffer.toString('base64');
  return `data:${mimeType};base64,${base64}`;
}

/**
 * Get MIME type from file extension
 */
function getMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.wav': 'audio/wav',
    '.mp3': 'audio/mpeg',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.webm': 'audio/webm',
  };
  return mimeTypes[ext] || 'audio/wav';
}

/**
 * Generate speech using Qwen3-TTS
 */
async function generateSpeech(options: TTSOptions): Promise<string> {
  const spinner = ora('Initializing Qwen3-TTS...').start();

  try {
    if (!process.env.REPLICATE_API_TOKEN) {
      throw new Error('REPLICATE_API_TOKEN is required in .env.local file');
    }

    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
    });

    // Build input based on mode
    const input: Record<string, unknown> = {
      text: options.text,
    };

    // Set the API mode
    input.mode = API_MODES[options.mode];

    switch (options.mode) {
      case 'voice':
        // Voice mode: use voice prompt/instruction for style
        spinner.text = 'Generating speech in Custom Voice mode...';
        if (options.voicePrompt) {
          input.voice_prompt = options.voicePrompt;
        }
        break;

      case 'clone':
        // Clone mode: use reference audio and text
        spinner.text = 'Generating speech in Voice Clone mode...';
        if (!options.refAudio) {
          throw new Error('Clone mode requires --ref-audio parameter');
        }
        if (!options.refText) {
          throw new Error('Clone mode requires --ref-text parameter');
        }
        
        // Check if ref_audio is a URL or file path
        if (options.refAudio.startsWith('http://') || options.refAudio.startsWith('https://')) {
          input.ref_audio = options.refAudio;
        } else {
          // Local file - convert to data URI
          if (!fs.existsSync(options.refAudio)) {
            throw new Error(`Reference audio file not found: ${options.refAudio}`);
          }
          const mimeType = getMimeType(options.refAudio);
          input.ref_audio = fileToDataUri(options.refAudio, mimeType);
          spinner.text = 'Uploaded reference audio...';
        }
        
        input.ref_text = options.refText;
        break;

      case 'design':
        // Design mode: create voice from description
        spinner.text = 'Generating speech in Voice Design mode...';
        if (!options.voiceDescription) {
          throw new Error('Design mode requires --voice-description parameter');
        }
        input.voice_description = options.voiceDescription;
        break;

      default:
        throw new Error(`Unknown mode: ${options.mode}`);
    }

    spinner.text = `Running Qwen3-TTS (${options.mode} mode)...`;
    
    // Create a prediction and wait for it to complete
    const prediction = await replicate.predictions.create({
      model: QWEN3_TTS_MODEL,
      input: input,
    });
    
    // Wait for the prediction to complete
    spinner.text = 'Waiting for audio generation...';
    let completedPrediction = await replicate.predictions.get(prediction.id);
    
    while (completedPrediction.status === 'starting' || completedPrediction.status === 'processing') {
      await new Promise(resolve => setTimeout(resolve, 1000));
      completedPrediction = await replicate.predictions.get(prediction.id);
      spinner.text = `Processing... (status: ${completedPrediction.status})`;
    }
    
    if (completedPrediction.status === 'failed') {
      throw new Error(`Prediction failed: ${completedPrediction.error || 'Unknown error'}`);
    }
    
    if (completedPrediction.status === 'canceled') {
      throw new Error('Prediction was canceled');
    }
    
    const output = completedPrediction.output;
    
    // Handle output - Replicate may return various formats
    let audioUrl: string | undefined;
    
    if (typeof output === 'string') {
      audioUrl = output;
    } else if (Array.isArray(output)) {
      // Array of URLs or single URL in array
      audioUrl = output.find(u => typeof u === 'string' && (u.includes('http') || u.includes('replicate')));
      if (!audioUrl && output.length > 0 && typeof output[0] === 'string') {
        audioUrl = output[0];
      }
    } else if (output && typeof output === 'object') {
      const obj = output as Record<string, unknown>;
      // Check various common field names
      const candidates = ['output', 'audio', 'audio_url', 'url', 'file', 'result'];
      for (const key of candidates) {
        const val = obj[key];
        if (typeof val === 'string' && val.length > 0) {
          audioUrl = val;
          break;
        } else if (Array.isArray(val) && val.length > 0) {
          const first = val.find((v: unknown) => typeof v === 'string');
          if (first) {
            audioUrl = first;
            break;
          }
        }
      }
    }

    if (!audioUrl) {
      throw new Error('Failed to extract audio URL from API response.');
    }

    // Handle output file
    const outputFolder = options.folder || 'public/audio';
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder, { recursive: true });
    }

    // Determine output filename and extension
    const urlPath = new URL(audioUrl).pathname;
    const urlExt = path.extname(urlPath) || '.wav';
    const filename = options.output || `qwen3-tts-${Date.now()}${urlExt}`;
    const outputPath = path.join(outputFolder, filename);

    spinner.text = 'Downloading generated audio...';
    await downloadFile(audioUrl, outputPath);

    spinner.succeed(chalk.green(`Audio generated successfully: ${outputPath}`));
    
    // Print summary
    console.log(chalk.cyan('\n📢 Speech Generation Summary:'));
    console.log(chalk.gray('  Mode:'), options.mode);
    console.log(chalk.gray('  Text:'), options.text.substring(0, 50) + (options.text.length > 50 ? '...' : ''));
    console.log(chalk.gray('  Output:'), outputPath);
    
    return outputPath;
  } catch (error: unknown) {
    spinner.fail(chalk.red(`Error generating speech: ${error instanceof Error ? error.message : 'Unknown error'}`));
    throw error;
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage('Usage: $0 [options]')
    .option('text', {
      alias: 't',
      type: 'string',
      description: 'Text to convert to speech',
      demandOption: true,
    })
    .option('mode', {
      alias: 'm',
      type: 'string',
      choices: ['voice', 'clone', 'design'] as const,
      description: 'TTS mode: voice (default), clone (voice cloning), or design (create voice from description)',
      default: 'voice',
    })
    .option('output', {
      alias: 'o',
      type: 'string',
      description: 'Output filename (default: qwen3-tts-<timestamp>.wav)',
    })
    .option('folder', {
      alias: 'f',
      type: 'string',
      description: 'Output folder path',
      default: 'public/audio',
    })
    .option('voice-prompt', {
      alias: 'v',
      type: 'string',
      description: '[Voice mode] Voice prompt/instruction for speech style (e.g., "speak cheerfully")',
    })
    .option('ref-audio', {
      alias: 'a',
      type: 'string',
      description: '[Clone mode] Path or URL to reference audio file (minimum 3 seconds)',
    })
    .option('ref-text', {
      alias: 'r',
      type: 'string',
      description: '[Clone mode] Transcript of the reference audio',
    })
    .option('voice-description', {
      alias: 'd',
      type: 'string',
      description: '[Design mode] Natural language description of desired voice (e.g., "warm female narrator with gentle pacing")',
    })
    .example([
      ['$0 -t "Hello, world!" -m voice', 'Generate speech with default voice'],
      ['$0 -t "Hello!" -m voice -v "speak with excitement"', 'Generate speech with style instruction'],
      ['$0 -t "Hello!" -m clone -a ref.wav -r "This is the reference text"', 'Clone a voice from audio'],
      ['$0 -t "Hello!" -m design -d "warm male storyteller voice"', 'Design a new voice'],
    ])
    .help()
    .alias('help', 'h')
    .argv;

  try {
    await generateSpeech({
      text: argv.text,
      mode: argv.mode as TTSMode,
      output: argv.output,
      folder: argv.folder,
      voicePrompt: argv['voice-prompt'],
      refAudio: argv['ref-audio'],
      refText: argv['ref-text'],
      voiceDescription: argv['voice-description'],
    });
  } catch (error) {
    process.exit(1);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});

export { generateSpeech, TTSOptions, TTSMode };
