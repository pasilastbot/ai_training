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

// p-video-avatar model identifier on Replicate
const VIDEO_AVATAR_MODEL = 'prunaai/p-video-avatar';

// Available voices
const VOICES = [
  'Zephyr (Female)', 'Puck (Male)', 'Charon (Male)', 'Kore (Female)', 
  'Fenrir (Male)', 'Leda (Female)', 'Orus (Male)', 'Aoede (Female)', 
  'Callirrhoe (Female)', 'Autonoe (Female)', 'Enceladus (Male)', 
  'Iapetus (Male)', 'Umbriel (Male)', 'Algenib (Male)', 'Despina (Female)', 
  'Erinome (Female)', 'Laomedeia (Female)', 'Achernar (Female)', 
  'Algieba (Male)', 'Schedar (Male)', 'Gacrux (Female)', 'Pulcherrima (Female)', 
  'Achird (Male)', 'Zubenelgenubi (Male)', 'Vindemiatrix (Female)', 
  'Sadachbia (Male)', 'Sadaltager (Male)', 'Sulafat (Female)', 
  'Alnilam (Male)', 'Rasalgethi (Male)'
] as const;

type Voice = typeof VOICES[number];

// Available languages
const LANGUAGES = [
  'English (US)', 'English (UK)', 'Spanish', 'French', 'German', 
  'Italian', 'Portuguese (Brazil)', 'Japanese', 'Korean', 'Hindi'
] as const;

type Language = typeof LANGUAGES[number];

// Resolution options
type Resolution = '720p' | '1080p';

interface VideoAvatarOptions {
  image: string;
  script?: string;
  audio?: string;
  voice?: Voice;
  language?: Language;
  voicePrompt?: string;
  videoPrompt?: string;
  resolution?: Resolution;
  output?: string;
  folder?: string;
  seed?: number;
  disableSafetyFilter?: boolean;
  disablePromptUpsampling?: boolean;
}

/**
 * Convert a local file to a base64 data URI
 */
function fileToDataUri(filePath: string, mimeType: string): string {
  const buffer = fs.readFileSync(filePath);
  const base64 = buffer.toString('base64');
  return `data:${mimeType};base64,${base64}`;
}

/**
 * Get MIME type from file extension for images
 */
function getImageMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
  };
  return mimeTypes[ext] || 'image/jpeg';
}

/**
 * Get MIME type from file extension for audio
 */
function getAudioMimeType(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes: Record<string, string> = {
    '.wav': 'audio/wav',
    '.mp3': 'audio/mpeg',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.webm': 'audio/webm',
  };
  return mimeTypes[ext] || 'audio/mpeg';
}

/**
 * Generate a talking-head video avatar from a portrait image
 */
async function generateVideoAvatar(options: VideoAvatarOptions): Promise<string> {
  const spinner = ora('Initializing p-video-avatar...').start();

  try {
    if (!process.env.REPLICATE_API_TOKEN) {
      throw new Error('REPLICATE_API_TOKEN is required in .env.local file');
    }

    // Validate: must have either script or audio
    if (!options.script && !options.audio) {
      throw new Error('Either --script or --audio is required');
    }

    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
    });

    // Build input
    const input: Record<string, unknown> = {
      resolution: options.resolution || '720p',
    };

    // Handle image input (required)
    spinner.text = 'Processing portrait image...';
    if (options.image.startsWith('http://') || options.image.startsWith('https://')) {
      input.image = options.image;
    } else {
      // Local file - convert to data URI
      if (!fs.existsSync(options.image)) {
        throw new Error(`Image file not found: ${options.image}`);
      }
      const mimeType = getImageMimeType(options.image);
      input.image = fileToDataUri(options.image, mimeType);
    }

    // Handle audio input (takes priority over script if both provided)
    if (options.audio) {
      spinner.text = 'Processing audio file...';
      if (options.audio.startsWith('http://') || options.audio.startsWith('https://')) {
        input.audio = options.audio;
      } else {
        // Local file - convert to data URI
        if (!fs.existsSync(options.audio)) {
          throw new Error(`Audio file not found: ${options.audio}`);
        }
        const mimeType = getAudioMimeType(options.audio);
        input.audio = fileToDataUri(options.audio, mimeType);
      }
    } else if (options.script) {
      // Use voice script with TTS
      input.voice_script = options.script;
      input.voice = options.voice || 'Zephyr (Female)';
      input.voice_language = options.language || 'English (US)';
      
      if (options.voicePrompt) {
        input.voice_prompt = options.voicePrompt;
      }
    }

    // Optional video prompt
    if (options.videoPrompt) {
      input.video_prompt = options.videoPrompt;
    }

    // Optional seed for reproducibility
    if (options.seed !== undefined) {
      input.seed = options.seed;
    }

    // Safety filter settings
    if (options.disableSafetyFilter !== undefined) {
      input.disable_safety_filter = options.disableSafetyFilter;
    }

    if (options.disablePromptUpsampling !== undefined) {
      input.disable_prompt_upsampling = options.disablePromptUpsampling;
    }

    spinner.text = `Generating video avatar (${options.resolution || '720p'})...`;
    
    // Create a prediction and wait for it to complete
    const prediction = await replicate.predictions.create({
      model: VIDEO_AVATAR_MODEL,
      input: input,
    });
    
    // Wait for the prediction to complete
    spinner.text = 'Processing video (this may take a few minutes)...';
    let completedPrediction = await replicate.predictions.get(prediction.id);
    
    while (completedPrediction.status === 'starting' || completedPrediction.status === 'processing') {
      await new Promise(resolve => setTimeout(resolve, 2000));
      completedPrediction = await replicate.predictions.get(prediction.id);
      spinner.text = `Processing video... (status: ${completedPrediction.status})`;
    }
    
    if (completedPrediction.status === 'failed') {
      throw new Error(`Prediction failed: ${completedPrediction.error || 'Unknown error'}`);
    }
    
    if (completedPrediction.status === 'canceled') {
      throw new Error('Prediction was canceled');
    }
    
    const output = completedPrediction.output;
    
    // Handle output - expect a video URL
    let videoUrl: string | undefined;
    
    if (typeof output === 'string') {
      videoUrl = output;
    } else if (Array.isArray(output)) {
      videoUrl = output.find(u => typeof u === 'string' && u.includes('http'));
      if (!videoUrl && output.length > 0 && typeof output[0] === 'string') {
        videoUrl = output[0];
      }
    } else if (output && typeof output === 'object') {
      const obj = output as Record<string, unknown>;
      const candidates = ['output', 'video', 'video_url', 'url', 'file', 'result'];
      for (const key of candidates) {
        const val = obj[key];
        if (typeof val === 'string' && val.length > 0) {
          videoUrl = val;
          break;
        }
      }
    }

    if (!videoUrl) {
      throw new Error('Failed to extract video URL from API response.');
    }

    // Handle output file
    const outputFolder = options.folder || 'public/videos';
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder, { recursive: true });
    }

    // Determine output filename
    const filename = options.output || `video-avatar-${Date.now()}.mp4`;
    const outputPath = path.join(outputFolder, filename);

    spinner.text = 'Downloading generated video...';
    await downloadFile(videoUrl, outputPath);

    spinner.succeed(chalk.green(`Video avatar generated successfully: ${outputPath}`));
    
    // Print summary
    console.log(chalk.cyan('\n🎬 Video Avatar Summary:'));
    console.log(chalk.gray('  Resolution:'), options.resolution || '720p');
    if (options.script) {
      console.log(chalk.gray('  Script:'), options.script.substring(0, 50) + (options.script.length > 50 ? '...' : ''));
      console.log(chalk.gray('  Voice:'), options.voice || 'Zephyr (Female)');
      console.log(chalk.gray('  Language:'), options.language || 'English (US)');
    } else if (options.audio) {
      console.log(chalk.gray('  Audio:'), options.audio);
    }
    console.log(chalk.gray('  Output:'), outputPath);
    
    // Estimate cost
    const costPerSecond = options.resolution === '1080p' ? 0.045 : 0.025;
    console.log(chalk.gray('  Cost rate:'), `$${costPerSecond}/second of output`);
    
    return outputPath;
  } catch (error: unknown) {
    spinner.fail(chalk.red(`Error generating video avatar: ${error instanceof Error ? error.message : 'Unknown error'}`));
    throw error;
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage('Usage: $0 [options]')
    .option('image', {
      alias: 'i',
      type: 'string',
      description: 'Path or URL to portrait image (required)',
      demandOption: true,
    })
    .option('script', {
      alias: 's',
      type: 'string',
      description: 'Text script for the avatar to speak (uses TTS)',
    })
    .option('audio', {
      alias: 'a',
      type: 'string',
      description: 'Path or URL to audio file for lip-sync (overrides script)',
    })
    .option('voice', {
      alias: 'V',
      type: 'string',
      choices: VOICES,
      description: 'Voice for TTS (default: Zephyr (Female))',
      default: 'Zephyr (Female)',
    })
    .option('language', {
      alias: 'l',
      type: 'string',
      choices: LANGUAGES,
      description: 'Language for TTS (default: English (US))',
      default: 'English (US)',
    })
    .option('voice-prompt', {
      alias: 'p',
      type: 'string',
      description: 'Speaking style instructions (e.g., "speak with excitement")',
    })
    .option('video-prompt', {
      type: 'string',
      description: 'Video prompt (e.g., "the person is gesturing with their hands")',
    })
    .option('resolution', {
      alias: 'r',
      type: 'string',
      choices: ['720p', '1080p'] as const,
      description: 'Output resolution (720p = $0.025/sec, 1080p = $0.045/sec)',
      default: '720p',
    })
    .option('output', {
      alias: 'o',
      type: 'string',
      description: 'Output filename (default: video-avatar-<timestamp>.mp4)',
    })
    .option('folder', {
      alias: 'f',
      type: 'string',
      description: 'Output folder path',
      default: 'public/videos',
    })
    .option('seed', {
      type: 'number',
      description: 'Random seed for reproducible generation',
    })
    .option('disable-safety-filter', {
      type: 'boolean',
      description: 'Disable safety filter for prompts and images',
      default: true,
    })
    .option('disable-prompt-upsampling', {
      type: 'boolean',
      description: 'Skip prompt upsampling (use raw prompt)',
      default: false,
    })
    .example([
      ['$0 -i portrait.jpg -s "Hello, welcome to our demo!"', 'Generate avatar with TTS'],
      ['$0 -i portrait.png -s "Bonjour!" -l French -V "Kore (Female)"', 'French avatar with custom voice'],
      ['$0 -i portrait.jpg -a speech.mp3', 'Lip-sync to existing audio'],
      ['$0 -i portrait.jpg -s "Hello!" -p "speak with enthusiasm" --video-prompt "person gestures"', 'With style prompts'],
      ['$0 -i portrait.jpg -s "Hello!" -r 1080p -o greeting.mp4', 'High-res with custom output'],
    ])
    .check((argv) => {
      if (!argv.script && !argv.audio) {
        throw new Error('Either --script or --audio is required');
      }
      return true;
    })
    .help()
    .alias('help', 'h')
    .argv;

  try {
    await generateVideoAvatar({
      image: argv.image,
      script: argv.script,
      audio: argv.audio,
      voice: argv.voice as Voice,
      language: argv.language as Language,
      voicePrompt: argv['voice-prompt'],
      videoPrompt: argv['video-prompt'],
      resolution: argv.resolution as Resolution,
      output: argv.output,
      folder: argv.folder,
      seed: argv.seed,
      disableSafetyFilter: argv['disable-safety-filter'],
      disablePromptUpsampling: argv['disable-prompt-upsampling'],
    });
  } catch (error) {
    process.exit(1);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});

export { generateVideoAvatar, VOICES, LANGUAGES };
export type { VideoAvatarOptions, Voice, Language, Resolution };
