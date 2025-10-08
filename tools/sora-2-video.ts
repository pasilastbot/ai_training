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

interface Sora2Options {
  prompt: string;
  seconds?: number;
  aspectRatio?: 'landscape' | 'portrait' | 'square';
  output?: string;
  folder?: string;
}

// Sora 2 model configuration
const SORA2_CONFIG = {
  model: 'openai/sora-2',
  description: 'OpenAI\'s flagship video generation model with synced audio',
  maxDuration: 20, // Based on typical Sora limits
  supportedAspectRatios: ['landscape', 'portrait', 'square'] as const,
  defaultAspectRatio: 'landscape' as const,
  defaultDuration: 8
};

async function generateSora2Video(options: Sora2Options): Promise<string> {
  const spinner = ora('Initializing Sora 2 video generation...').start();

  try {
    // Validate required API keys
    if (!process.env.REPLICATE_API_TOKEN) {
      throw new Error('REPLICATE_API_TOKEN is required in .env file');
    }

    if (!process.env.OPENAI_API_KEY) {
      throw new Error('OPENAI_API_KEY is required in .env file for Sora 2');
    }

    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
    });

    // Validate duration
    const duration = options.seconds || SORA2_CONFIG.defaultDuration;
    if (duration > SORA2_CONFIG.maxDuration) {
      throw new Error(`Maximum duration for Sora 2 is ${SORA2_CONFIG.maxDuration} seconds`);
    }

    // Validate aspect ratio
    const aspectRatio = options.aspectRatio || SORA2_CONFIG.defaultAspectRatio;
    if (!SORA2_CONFIG.supportedAspectRatios.includes(aspectRatio)) {
      throw new Error(`Aspect ratio ${aspectRatio} not supported. Supported ratios: ${SORA2_CONFIG.supportedAspectRatios.join(', ')}`);
    }

    // Prepare input for Sora 2 API
    const input = {
      prompt: options.prompt,
      seconds: duration,
      aspect_ratio: aspectRatio,
      openai_api_key: process.env.OPENAI_API_KEY
    };

    spinner.text = `Generating ${duration}s video with Sora 2...`;
    console.log(chalk.blue(`\nPrompt: "${options.prompt}"`));
    console.log(chalk.blue(`Duration: ${duration} seconds`));
    console.log(chalk.blue(`Aspect Ratio: ${aspectRatio}`));

    const output = await replicate.run(SORA2_CONFIG.model, { input });

    // Handle output - Sora 2 returns a file object with url() method
    if (!output || typeof output.url !== 'function') {
      throw new Error('Invalid output from Sora 2 API - expected file object with url() method');
    }

    const videoUrl = output.url();
    if (!videoUrl) {
      throw new Error('Failed to get video URL from Sora 2 output');
    }

    // Setup output path
    const outputFolder = options.folder || 'public/videos';
    if (!fs.existsSync(outputFolder)) {
      fs.mkdirSync(outputFolder, { recursive: true });
    }

    const filename = options.output || `sora2-generated-${Date.now()}.mp4`;
    const outputPath = path.join(outputFolder, filename);

    spinner.text = 'Downloading generated video...';
    
    // Write the file to disk using the Replicate file object
    await writeFile(outputPath, output);

    spinner.succeed(chalk.green(`Sora 2 video generated successfully: ${outputPath}`));
    console.log(chalk.cyan(`Video URL: ${videoUrl}`));
    
    return outputPath;
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    spinner.fail(chalk.red(`Error generating Sora 2 video: ${errorMessage}`));
    
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
    .option('seconds', {
      alias: 's',
      type: 'number',
      description: `Duration of the video in seconds (max: ${SORA2_CONFIG.maxDuration})`,
      default: SORA2_CONFIG.defaultDuration
    })
    .option('aspect-ratio', {
      alias: 'a',
      type: 'string',
      choices: SORA2_CONFIG.supportedAspectRatios,
      description: 'Aspect ratio of the video',
      default: SORA2_CONFIG.defaultAspectRatio
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
    .example('$0 -p "A cat playing piano in a jazz club"', 'Generate a video with default settings')
    .example('$0 -p "Sunset over mountains" -s 15 -a portrait -o sunset.mp4', 'Generate a 15-second portrait video')
    .help()
    .argv;

  try {
    await generateSora2Video({
      prompt: argv.prompt,
      seconds: argv.seconds,
      aspectRatio: argv['aspect-ratio'] as 'landscape' | 'portrait' | 'square',
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

export { generateSora2Video, SORA2_CONFIG };
