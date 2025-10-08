import Replicate from 'replicate';
import { config } from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import ora from 'ora';
import chalk from 'chalk';
import * as path from 'path';
import * as fs from 'fs';
import { writeFile } from 'fs/promises';

// Load environment variables
config({ path: '.env.local' });
config({ path: '.env' });

interface Veo3Options {
  prompt: string;
  image?: string;
  seed?: number;
  resolution?: '720p' | '1080p';
  negativePrompt?: string;
  aspectRatio?: '16:9' | '9:16' | '4:3' | '1:1';
  duration?: number;
  fps?: number;
  generateAudio?: boolean;
  output?: string;
  folder?: string;
}

// Veo 3 Fast model configuration
const VEO3_CONFIG = {
  model: 'google/veo-3-fast',
  description: 'A faster and cheaper version of Google\'s Veo 3 video model, with audio',
  maxDuration: 30, // Based on typical video generation limits
  supportedResolutions: ['720p', '1080p'] as const,
  supportedAspectRatios: ['16:9', '9:16', '4:3', '1:1'] as const,
  supportedFps: [24, 30] as const,
  defaultResolution: '720p' as const,
  defaultAspectRatio: '16:9' as const,
  defaultDuration: 8,
  defaultFps: 24
};

async function generateVeo3Video(options: Veo3Options): Promise<string> {
  const spinner = ora('Initializing Veo 3 Fast video generation...').start();

  try {
    // Validate required API key
    if (!process.env.REPLICATE_API_TOKEN) {
      throw new Error('REPLICATE_API_TOKEN is required in .env file');
    }

    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
    });

    // Validate duration
    const duration = options.duration || VEO3_CONFIG.defaultDuration;
    if (duration > VEO3_CONFIG.maxDuration) {
      throw new Error(`Maximum duration for Veo 3 Fast is ${VEO3_CONFIG.maxDuration} seconds`);
    }

    // Validate resolution
    const resolution = options.resolution || VEO3_CONFIG.defaultResolution;
    if (!VEO3_CONFIG.supportedResolutions.includes(resolution)) {
      throw new Error(`Resolution ${resolution} not supported. Supported resolutions: ${VEO3_CONFIG.supportedResolutions.join(', ')}`);
    }

    // Validate aspect ratio
    const aspectRatio = options.aspectRatio || VEO3_CONFIG.defaultAspectRatio;
    if (!VEO3_CONFIG.supportedAspectRatios.includes(aspectRatio)) {
      throw new Error(`Aspect ratio ${aspectRatio} not supported. Supported ratios: ${VEO3_CONFIG.supportedAspectRatios.join(', ')}`);
    }

    // Validate FPS
    const fps = options.fps || VEO3_CONFIG.defaultFps;
    if (!VEO3_CONFIG.supportedFps.includes(fps as 24 | 30)) {
      throw new Error(`FPS ${fps} not supported. Supported FPS: ${VEO3_CONFIG.supportedFps.join(', ')}`);
    }

    // Prepare input for Veo 3 Fast API
    const input: any = {
      prompt: options.prompt,
      duration: duration,
      resolution: resolution,
      aspect_ratio: aspectRatio,
      fps: fps
    };

    // Add image input if provided
    if (options.image) {
      input.image = options.image;
    }

    // Add optional parameters
    if (options.seed !== undefined) {
      input.seed = options.seed;
    }

    if (options.negativePrompt) {
      input.negative_prompt = options.negativePrompt;
    }

    if (options.generateAudio) {
      input.generate_audio = true;
    }

    spinner.text = `Generating ${duration}s video with Veo 3 Fast...`;
    console.log(chalk.blue(`\nPrompt: "${options.prompt}"`));
    console.log(chalk.blue(`Duration: ${duration} seconds`));
    console.log(chalk.blue(`Resolution: ${resolution}`));
    console.log(chalk.blue(`Aspect Ratio: ${aspectRatio}`));
    console.log(chalk.blue(`FPS: ${fps}`));
    console.log(chalk.blue(`Audio: ${options.generateAudio ? 'Yes' : 'No'}`));
    if (options.seed !== undefined) {
      console.log(chalk.blue(`Seed: ${options.seed}`));
    }

    const output = await replicate.run(VEO3_CONFIG.model, { input });

    // Handle output - Veo 3 Fast returns a file object with url() method
    if (!output || typeof output.url !== 'function') {
      throw new Error('Invalid output from Veo 3 Fast API - expected file object with url() method');
    }

    const videoUrl = output.url();
    if (!videoUrl) {
      throw new Error('Failed to get video URL from Veo 3 Fast output');
    }

    // Setup output path
    const outputFolder = options.folder || 'public/videos';
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder, { recursive: true });
    }

    const filename = options.output || `veo3-generated-${Date.now()}.mp4`;
    const outputPath = path.join(outputFolder, filename);

    spinner.text = 'Downloading generated video...';
    
    // Write the file to disk using the Replicate file object
    await writeFile(outputPath, output);

    spinner.succeed(chalk.green(`Veo 3 Fast video generated successfully: ${outputPath}`));
    console.log(chalk.cyan(`Video URL: ${videoUrl}`));
    
    return outputPath;
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    spinner.fail(chalk.red(`Error generating Veo 3 Fast video: ${errorMessage}`));
    
    // Enhanced error logging for debugging
    if (error instanceof Error) {
      console.error(chalk.red('Detailed error:'), error);
      if ('response' in (error as any)) {
        console.error(chalk.red('API Response:'), (error as any).response?.data);
      }
    }
    
    throw error;
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .option('prompt', {
      alias: 'p',
      type: 'string',
      description: 'Text description of the desired video',
      demandOption: true
    })
    .option('image', {
      alias: 'i',
      type: 'string',
      description: 'URL or path to input image for image-to-video generation'
    })
    .option('seed', {
      type: 'number',
      description: 'Random seed for reproducibility'
    })
    .option('resolution', {
      alias: 'r',
      type: 'string',
      choices: VEO3_CONFIG.supportedResolutions,
      description: 'Resolution of the generated video',
      default: VEO3_CONFIG.defaultResolution
    })
    .option('negative-prompt', {
      alias: 'n',
      type: 'string',
      description: 'Description of what to discourage in the generated video'
    })
    .option('aspect-ratio', {
      alias: 'a',
      type: 'string',
      choices: VEO3_CONFIG.supportedAspectRatios,
      description: 'Aspect ratio of the video',
      default: VEO3_CONFIG.defaultAspectRatio
    })
    .option('duration', {
      alias: 'd',
      type: 'number',
      description: `Duration of the video in seconds (max: ${VEO3_CONFIG.maxDuration})`,
      default: VEO3_CONFIG.defaultDuration
    })
    .option('fps', {
      type: 'number',
      choices: VEO3_CONFIG.supportedFps,
      description: 'Frames per second',
      default: VEO3_CONFIG.defaultFps
    })
    .option('generate-audio', {
      type: 'boolean',
      description: 'Generate synchronized audio with the video',
      default: false
    })
    .option('output', {
      alias: 'o',
      type: 'string',
      description: 'Output filename for the video'
    })
    .option('folder', {
      alias: 'f',
      type: 'string',
      description: 'Output folder path',
      default: 'public/videos'
    })
    .example('$0 -p "A serene forest at dawn with mist"', 'Generate a video with default settings')
    .example('$0 -p "Ocean waves at sunset" -r 1080p -d 10 --generate-audio', 'Generate a 10-second 1080p video with audio')
    .example('$0 -p "Rotate the shoe, keep everything else still" -i "https://example.com/shoe.png"', 'Generate video from image input')
    .example('$0 -p "City skyline timelapse" -a 16:9 --fps 30 --seed 42', 'Generate with specific aspect ratio, FPS, and seed')
    .help()
    .argv;

  try {
    await generateVeo3Video({
      prompt: argv.prompt,
      image: argv.image,
      seed: argv.seed,
      resolution: argv.resolution as '720p' | '1080p',
      negativePrompt: argv['negative-prompt'],
      aspectRatio: argv['aspect-ratio'] as '16:9' | '9:16' | '4:3' | '1:1',
      duration: argv.duration,
      fps: argv.fps as 24 | 30,
      generateAudio: argv['generate-audio'],
      output: argv.output,
      folder: argv.folder
    });
  } catch (error) {
    console.error(chalk.red('Failed to generate video'));
    process.exit(1);
  }
}

// Execute main function if this file is run directly
main().catch(error => {
  console.error(error);
  process.exit(1);
});

export { generateVeo3Video, VEO3_CONFIG };
