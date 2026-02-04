#!/usr/bin/env node

/**
 * Sprite Animation Generator
 * 
 * Generate animation frames for game sprites using AI models.
 * Creates multiple frames for animations like walking, jumping, idle, etc.
 * 
 * Usage:
 *   npm run sprite-animator -- --character "pixel art knight" --animation walk --frames 8
 *   npm run sprite-animator -- --character "cute dragon" --animation fly --frames 6 --style "32x32 pixel art"
 */

import * as dotenv from 'dotenv';
import { Command } from 'commander';
import Replicate from 'replicate';
import fetch from 'node-fetch';
import * as fs from 'fs';
import * as path from 'path';
import sharp from 'sharp';

dotenv.config({ path: '.env.local' });

interface AnimationFrame {
  frameNumber: number;
  prompt: string;
  imagePath: string;
}

interface SpriteAnimationOptions {
  character: string;
  animation: string;
  frames: number;
  style: string;
  output?: string;
  folder: string;
  model: string;
  spriteSheet: boolean;
  size: string;
  transparent: boolean;
}

const ANIMATION_PROMPTS: Record<string, (character: string, frame: number, total: number) => string> = {
  walk: (char, f, total) => {
    const cycle = ['left leg forward', 'neutral stance', 'right leg forward', 'neutral stance'];
    const pos = Math.floor((f / total) * cycle.length) % cycle.length;
    return `${char}, walking animation frame, ${cycle[pos]}, side view`;
  },
  run: (char, f, total) => {
    const cycle = ['both legs tucked', 'left leg extended forward', 'mid-stride', 'right leg extended forward'];
    const pos = Math.floor((f / total) * cycle.length) % cycle.length;
    return `${char}, running animation frame, ${cycle[pos]}, dynamic pose, side view`;
  },
  jump: (char, f, total) => {
    const progress = f / (total - 1);
    if (progress < 0.2) return `${char}, crouching down, preparing to jump`;
    if (progress < 0.4) return `${char}, launching upward, legs pushing off`;
    if (progress < 0.6) return `${char}, at peak of jump, airborne, legs tucked`;
    if (progress < 0.8) return `${char}, descending, legs preparing to land`;
    return `${char}, landing pose, knees bent`;
  },
  idle: (char, f, total) => {
    const progress = f / (total - 1);
    const breathe = Math.sin(progress * Math.PI * 2);
    return `${char}, idle standing pose, subtle breathing motion ${breathe > 0 ? 'inhaling' : 'exhaling'}`;
  },
  attack: (char, f, total) => {
    const progress = f / (total - 1);
    if (progress < 0.3) return `${char}, preparing attack, weapon raised`;
    if (progress < 0.5) return `${char}, mid-attack, weapon swinging`;
    if (progress < 0.7) return `${char}, attack follow-through, weapon extended`;
    return `${char}, recovering from attack, returning to stance`;
  },
  fly: (char, f, total) => {
    const cycle = ['wings up', 'wings level', 'wings down', 'wings level'];
    const pos = Math.floor((f / total) * cycle.length) % cycle.length;
    return `${char}, flying animation frame, ${cycle[pos]}, airborne`;
  },
  swim: (char, f, total) => {
    const cycle = ['arms forward', 'arms pulling back', 'arms at sides', 'arms returning forward'];
    const pos = Math.floor((f / total) * cycle.length) % cycle.length;
    return `${char}, swimming animation frame, ${cycle[pos]}, horizontal position`;
  },
  death: (char, f, total) => {
    const progress = f / (total - 1);
    if (progress < 0.3) return `${char}, hit reaction, recoiling`;
    if (progress < 0.6) return `${char}, falling, losing balance`;
    return `${char}, on ground, defeated pose`;
  },
};

async function downloadImage(url: string, outputPath: string): Promise<void> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to download image: ${response.statusText}`);
  }
  const buffer = await response.arrayBuffer();
  await fs.promises.writeFile(outputPath, Buffer.from(buffer));
}

async function removeBackground(inputPath: string, outputPath: string): Promise<void> {
  try {
    // Use Sharp to remove white/light backgrounds
    const image = sharp(inputPath);
    const metadata = await image.metadata();
    
    // Convert to PNG with transparency
    await image
      .removeAlpha()
      .ensureAlpha()
      .raw()
      .toBuffer({ resolveWithObject: true })
      .then(({ data, info }) => {
        const pixels = new Uint8Array(data);
        const threshold = 240; // White/light color threshold
        
        for (let i = 0; i < pixels.length; i += info.channels) {
          const r = pixels[i];
          const g = pixels[i + 1];
          const b = pixels[i + 2];
          
          // If pixel is close to white, make it transparent
          if (r > threshold && g > threshold && b > threshold) {
            pixels[i + 3] = 0; // Set alpha to 0
          }
        }
        
        return sharp(pixels, {
          raw: {
            width: info.width,
            height: info.height,
            channels: info.channels,
          },
        })
          .png()
          .toFile(outputPath);
      });
  } catch (error) {
    console.warn('Background removal failed, copying original:', error);
    await fs.promises.copyFile(inputPath, outputPath);
  }
}

async function createSpriteSheet(frames: AnimationFrame[], outputPath: string, size: string): Promise<void> {
  const [width, height] = size.split('x').map(Number);
  const framesPerRow = Math.ceil(Math.sqrt(frames.length));
  const rows = Math.ceil(frames.length / framesPerRow);
  
  const sheetWidth = width * framesPerRow;
  const sheetHeight = height * rows;
  
  // Create blank sprite sheet
  const sheet = sharp({
    create: {
      width: sheetWidth,
      height: sheetHeight,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  });
  
  // Composite all frames
  const composites = await Promise.all(
    frames.map(async (frame, index) => {
      const col = index % framesPerRow;
      const row = Math.floor(index / framesPerRow);
      
      const resized = await sharp(frame.imagePath)
        .resize(width, height, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .toBuffer();
      
      return {
        input: resized,
        left: col * width,
        top: row * height,
      };
    })
  );
  
  await sheet.composite(composites).png().toFile(outputPath);
  console.log(`✅ Sprite sheet created: ${outputPath}`);
  console.log(`   Grid: ${framesPerRow}x${rows} (${sheetWidth}x${sheetHeight}px)`);
}

async function generateSpriteAnimation(options: SpriteAnimationOptions): Promise<void> {
  const {
    character,
    animation,
    frames: frameCount,
    style,
    output,
    folder,
    model,
    spriteSheet,
    size,
    transparent,
  } = options;
  
  const replicate = new Replicate({
    auth: process.env.REPLICATE_API_TOKEN,
  });
  
  // Ensure output folder exists
  await fs.promises.mkdir(folder, { recursive: true });
  
  const animationGenerator = ANIMATION_PROMPTS[animation.toLowerCase()];
  if (!animationGenerator) {
    throw new Error(
      `Unknown animation type: ${animation}. Available: ${Object.keys(ANIMATION_PROMPTS).join(', ')}`
    );
  }
  
  console.log(`🎬 Generating ${frameCount} frames for ${animation} animation...`);
  console.log(`   Character: ${character}`);
  console.log(`   Style: ${style}`);
  console.log(`   Model: ${model}`);
  
  const generatedFrames: AnimationFrame[] = [];
  
  // Generate each frame
  for (let i = 0; i < frameCount; i++) {
    const framePrompt = animationGenerator(character, i, frameCount);
    const fullPrompt = `${framePrompt}, ${style}, consistent character design, clean lines, game sprite`;
    
    console.log(`\n📸 Frame ${i + 1}/${frameCount}: ${framePrompt}`);
    
    try {
      let imageUrl: string;
      
      if (model === 'flux-schnell') {
        const output = await replicate.run('black-forest-labs/flux-schnell' as any, {
          input: {
            prompt: fullPrompt,
            num_outputs: 1,
          },
        }) as any;
        imageUrl = Array.isArray(output) ? output[0] : output;
      } else if (model === 'sdxl') {
        const output = await replicate.run('stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b' as any, {
          input: {
            prompt: fullPrompt,
            num_outputs: 1,
          },
        }) as any;
        imageUrl = Array.isArray(output) ? output[0] : output;
      } else {
        throw new Error(`Unsupported model: ${model}`);
      }
      
      // Download frame
      const frameName = `frame_${String(i).padStart(3, '0')}.png`;
      const framePath = path.join(folder, frameName);
      await downloadImage(imageUrl, framePath);
      
      // Remove background if requested
      if (transparent) {
        const transparentPath = path.join(folder, `transparent_${frameName}`);
        await removeBackground(framePath, transparentPath);
        generatedFrames.push({
          frameNumber: i,
          prompt: framePrompt,
          imagePath: transparentPath,
        });
      } else {
        generatedFrames.push({
          frameNumber: i,
          prompt: framePrompt,
          imagePath: framePath,
        });
      }
      
      console.log(`   ✅ Saved: ${frameName}`);
    } catch (error) {
      console.error(`   ❌ Failed to generate frame ${i + 1}:`, error);
      throw error;
    }
  }
  
  // Create sprite sheet if requested
  if (spriteSheet) {
    const sheetName = output || `${animation}_sprite_sheet.png`;
    const sheetPath = path.join(folder, sheetName);
    await createSpriteSheet(generatedFrames, sheetPath, size);
  }
  
  // Save animation metadata
  const metadataPath = path.join(folder, `${animation}_animation.json`);
  const metadata = {
    character,
    animation,
    frameCount,
    style,
    size,
    transparent,
    generatedAt: new Date().toISOString(),
    frames: generatedFrames.map((f) => ({
      number: f.frameNumber,
      prompt: f.prompt,
      file: path.basename(f.imagePath),
    })),
  };
  await fs.promises.writeFile(metadataPath, JSON.stringify(metadata, null, 2));
  
  console.log(`\n✅ Animation generation complete!`);
  console.log(`   Frames: ${folder}`);
  console.log(`   Metadata: ${metadataPath}`);
  if (spriteSheet) {
    console.log(`   Sprite sheet: ${path.join(folder, output || `${animation}_sprite_sheet.png`)}`);
  }
}

const program = new Command();

program
  .name('sprite-animator')
  .description('Generate sprite animation frames for games using AI')
  .requiredOption('-c, --character <description>', 'Character description (e.g., "pixel art knight")')
  .requiredOption(
    '-a, --animation <type>',
    `Animation type: ${Object.keys(ANIMATION_PROMPTS).join(', ')}`
  )
  .option('-n, --frames <number>', 'Number of frames to generate', '8')
  .option('-s, --style <style>', 'Art style description', 'pixel art, 2D game sprite, centered, white background')
  .option('-o, --output <filename>', 'Output filename for sprite sheet')
  .option('-f, --folder <path>', 'Output folder', 'public/sprites')
  .option(
    '-m, --model <model>',
    'Model to use: flux-schnell (fast), sdxl (quality)',
    'flux-schnell'
  )
  .option('--sprite-sheet', 'Create a sprite sheet from frames', false)
  .option('--size <size>', 'Size of each frame in sprite sheet (WxH)', '64x64')
  .option('--transparent', 'Attempt to remove background (white/light colors)', false)
  .parse();

const options = program.opts();

generateSpriteAnimation({
  character: options.character,
  animation: options.animation,
  frames: parseInt(options.frames, 10),
  style: options.style,
  output: options.output,
  folder: options.folder,
  model: options.model,
  spriteSheet: options.spriteSheet,
  size: options.size,
  transparent: options.transparent,
}).catch((error) => {
  console.error('❌ Error:', error.message);
  process.exit(1);
});
