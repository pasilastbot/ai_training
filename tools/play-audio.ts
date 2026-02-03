import { config } from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import chalk from 'chalk';
import * as path from 'path';
import * as fs from 'fs';
import { spawn } from 'child_process';
import * as os from 'os';

// Load environment variables
config({
  path: process.env.NODE_ENV === 'development' ? '.env.local' : '.env'
});

interface PlayOptions {
  file: string;
  volume?: number;
  wait?: boolean;
}

/**
 * Get the appropriate audio player command for the current platform
 */
function getAudioPlayer(): { command: string; args: (file: string, volume?: number) => string[] } | null {
  const platform = os.platform();
  
  switch (platform) {
    case 'darwin':
      // macOS - use afplay
      return {
        command: 'afplay',
        args: (file: string, volume?: number) => {
          const args = [file];
          if (volume !== undefined) {
            // afplay volume is 0-255, we accept 0-100
            const vol = Math.round((volume / 100) * 255);
            args.push('-v', vol.toString());
          }
          return args;
        }
      };
    
    case 'linux':
      // Linux - try paplay (PulseAudio) first, fallback to aplay
      return {
        command: 'paplay',
        args: (file: string, volume?: number) => {
          const args = [file];
          if (volume !== undefined) {
            // paplay uses percentage
            args.push('--volume', Math.round((volume / 100) * 65536).toString());
          }
          return args;
        }
      };
    
    case 'win32':
      // Windows - use PowerShell
      return {
        command: 'powershell',
        args: (file: string) => [
          '-c',
          `(New-Object Media.SoundPlayer '${file.replace(/'/g, "''")}').PlaySync()`
        ]
      };
    
    default:
      return null;
  }
}

/**
 * Play an audio file
 */
async function playAudio(options: PlayOptions): Promise<void> {
  const { file, volume, wait = true } = options;

  // Resolve file path
  const filePath = path.resolve(file);
  
  // Check if file exists
  if (!fs.existsSync(filePath)) {
    throw new Error(`Audio file not found: ${filePath}`);
  }

  // Get file extension
  const ext = path.extname(filePath).toLowerCase();
  const supportedFormats = ['.wav', '.mp3', '.m4a', '.aac', '.aiff', '.ogg', '.flac'];
  
  if (!supportedFormats.includes(ext)) {
    console.log(chalk.yellow(`Warning: ${ext} format may not be supported on all platforms`));
  }

  // Get audio player for current platform
  const player = getAudioPlayer();
  
  if (!player) {
    throw new Error(`Unsupported platform: ${os.platform()}`);
  }

  console.log(chalk.cyan('🔊 Playing audio:'), filePath);
  if (volume !== undefined) {
    console.log(chalk.gray('   Volume:'), `${volume}%`);
  }

  return new Promise((resolve, reject) => {
    const args = player.args(filePath, volume);
    const proc = spawn(player.command, args, {
      stdio: wait ? 'inherit' : 'ignore',
      detached: !wait
    });

    if (!wait) {
      proc.unref();
      console.log(chalk.green('✔ Audio playback started in background'));
      resolve();
      return;
    }

    proc.on('error', (err) => {
      // If paplay fails on Linux, try aplay
      if (player.command === 'paplay' && os.platform() === 'linux') {
        console.log(chalk.yellow('paplay not found, trying aplay...'));
        const aplayProc = spawn('aplay', [filePath], { stdio: 'inherit' });
        aplayProc.on('error', reject);
        aplayProc.on('close', (code) => {
          if (code === 0) {
            console.log(chalk.green('✔ Audio playback completed'));
            resolve();
          } else {
            reject(new Error(`aplay exited with code ${code}`));
          }
        });
        return;
      }
      reject(err);
    });

    proc.on('close', (code) => {
      if (code === 0) {
        console.log(chalk.green('✔ Audio playback completed'));
        resolve();
      } else {
        reject(new Error(`${player.command} exited with code ${code}`));
      }
    });
  });
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage('Usage: $0 <file> [options]')
    .positional('file', {
      type: 'string',
      description: 'Path to audio file to play',
    })
    .option('file', {
      alias: 'f',
      type: 'string',
      description: 'Path to audio file to play (alternative to positional)',
    })
    .option('volume', {
      alias: 'v',
      type: 'number',
      description: 'Volume level (0-100)',
      default: undefined,
    })
    .option('background', {
      alias: 'b',
      type: 'boolean',
      description: 'Play in background (do not wait for completion)',
      default: false,
    })
    .example([
      ['$0 audio.wav', 'Play audio.wav'],
      ['$0 -f public/audio/speech.wav', 'Play with -f flag'],
      ['$0 audio.mp3 -v 50', 'Play at 50% volume'],
      ['$0 audio.wav -b', 'Play in background'],
    ])
    .help()
    .alias('help', 'h')
    .argv;

  // Get file from positional argument or -f flag
  const file = argv._[0]?.toString() || argv.file;
  
  if (!file) {
    console.error(chalk.red('Error: Please provide an audio file path'));
    console.log('Usage: npm run play-audio -- <file> [options]');
    process.exit(1);
  }

  try {
    await playAudio({
      file,
      volume: argv.volume,
      wait: !argv.background,
    });
  } catch (error) {
    console.error(chalk.red(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`));
    process.exit(1);
  }
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});

export { playAudio, PlayOptions };
