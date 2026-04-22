import Replicate from 'replicate';
import { config } from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import ora from 'ora';
import chalk from 'chalk';
import * as path from 'path';
import * as fs from 'fs';
import { randomUUID } from 'crypto';
import sharp from 'sharp';
import { downloadFile } from './utils/download';

config({
  path: process.env.NODE_ENV === 'development' ? '.env.local' : '.env',
});

/** Pinned so `replicate.run` uses POST /v1/predictions (model-only route 404s for this Cog model). Bump from [model page](https://replicate.com/adirik/grounding-dino). */
const MODEL_REF =
  'adirik/grounding-dino:efd10a8ddc57ea28773327e881ce95e20cc1d734c589f7dd01d2036921ed78aa' as const;

export interface Detection {
  bbox: [number, number, number, number];
  label: string;
  confidence: number;
}

export interface GroundingDinoResult {
  detections: Detection[];
  result_image?: string;
  /** Paths written by `cropDetections` when `crop` is set on `detectObjects` */
  cropPaths?: string[];
}

export interface CropOptions {
  /** If set, only detections whose label contains this substring (case-insensitive) */
  labelFilter?: string;
  outputDir: string;
  format?: 'png' | 'jpeg';
}

export interface GroundingDinoOptions {
  /** HTTPS URL — image is fetched with the same downloader as `npm run download-file` */
  url?: string;
  /** Local image path (skips download) */
  image?: string;
  /** Comma-separated object names / phrases to find */
  query: string;
  boxThreshold?: number;
  textThreshold?: number;
  /** When true, API returns `result_image` with boxes drawn */
  showVisualisation?: boolean;
  /** Print JSON only (no spinner styling) */
  json?: boolean;
  /** After detection, crop each bbox (optionally filtered by label) with Sharp */
  crop?: CropOptions;
}

function extFromUrl(url: string): string {
  const base = path.basename(url.split('?')[0]);
  const ext = path.extname(base);
  return ext || '.jpg';
}

function normalizeOutput(output: unknown): GroundingDinoResult {
  if (output == null || typeof output !== 'object') {
    throw new Error('Empty or invalid model output');
  }
  const o = output as Record<string, unknown>;
  const raw = o.detections;
  if (!Array.isArray(raw)) {
    throw new Error('Expected output.detections array');
  }
  const detections: Detection[] = raw.map((item) => {
    const d = item as Record<string, unknown>;
    const bbox = d.bbox;
    if (!Array.isArray(bbox) || bbox.length !== 4) {
      throw new Error('Invalid detection bbox');
    }
    return {
      bbox: bbox as [number, number, number, number],
      label: String(d.label ?? ''),
      confidence: Number(d.confidence ?? 0),
    };
  });
  return {
    detections,
    result_image: typeof o.result_image === 'string' ? o.result_image : undefined,
  };
}

function slugifyLabel(s: string): string {
  const t = s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return t.length > 0 ? t : 'item';
}

/**
 * Cut out rectangular regions from `imagePath` for each detection (optionally filtered by label substring).
 * Bboxes are assumed to be pixel coordinates [x1, y1, x2, y2] in the same space as the image.
 */
export async function cropDetections(
  imagePath: string,
  detections: Detection[],
  options: CropOptions,
): Promise<string[]> {
  const { labelFilter, outputDir, format = 'png' } = options;
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  const needle = labelFilter?.trim().toLowerCase();
  const matches = needle
    ? detections.filter((d) => d.label.toLowerCase().includes(needle))
    : [...detections];

  const meta = await sharp(imagePath).metadata();
  const iw = meta.width ?? 0;
  const ih = meta.height ?? 0;
  if (iw < 1 || ih < 1) {
    throw new Error('Could not read image dimensions');
  }

  const outPaths: string[] = [];
  for (let i = 0; i < matches.length; i++) {
    const d = matches[i];
    const [a, b, c, e] = d.bbox;
    const left = Math.max(0, Math.floor(Math.min(a, c)));
    const top = Math.max(0, Math.floor(Math.min(b, e)));
    const right = Math.min(iw, Math.ceil(Math.max(a, c)));
    const bottom = Math.min(ih, Math.ceil(Math.max(b, e)));
    const width = right - left;
    const height = bottom - top;
    if (width < 1 || height < 1) {
      continue;
    }

    const base = `${slugifyLabel(d.label)}-${String(i + 1).padStart(2, '0')}`;
    const ext = format === 'jpeg' ? '.jpg' : '.png';
    const outPath = path.join(outputDir, `${base}${ext}`);

    let pipeline = sharp(imagePath).extract({ left, top, width, height });
    pipeline = format === 'jpeg' ? pipeline.jpeg({ quality: 92 }) : pipeline.png();
    await pipeline.toFile(outPath);
    outPaths.push(outPath);
  }
  return outPaths;
}

/**
 * Download image from URL (via shared `utils/download`) and run Grounding DINO, or use a local file.
 */
export async function detectObjects(options: GroundingDinoOptions): Promise<GroundingDinoResult> {
  if (!process.env.REPLICATE_API_TOKEN) {
    throw new Error('REPLICATE_API_TOKEN is required in .env.local');
  }

  const { url, image, query } = options;
  if (!query.trim()) {
    throw new Error('query must not be empty');
  }
  if (url && image) {
    throw new Error('Use either --url or --image, not both');
  }
  if (!url && !image) {
    throw new Error('Provide --url or --image');
  }

  let imagePath: string;
  let tempPath: string | undefined;

  if (image) {
    if (!fs.existsSync(image)) {
      throw new Error(`Image not found: ${image}`);
    }
    imagePath = path.resolve(image);
  } else {
    const folder = path.join('downloads', 'grounding-dino-temp');
    if (!fs.existsSync(folder)) {
      fs.mkdirSync(folder, { recursive: true });
    }
    tempPath = path.join(folder, `grounding-${randomUUID()}${extFromUrl(url!)}`);
    await downloadFile(url!, tempPath);
    imagePath = tempPath;
  }

  try {
    const replicate = new Replicate({
      auth: process.env.REPLICATE_API_TOKEN,
      useFileOutput: false,
    });

    const boxThreshold = options.boxThreshold ?? 0.25;
    const textThreshold = options.textThreshold ?? 0.25;
    const showVisualisation = options.showVisualisation ?? true;

    const output = await replicate.run(MODEL_REF, {
      input: {
        image: fs.readFileSync(imagePath),
        query,
        box_threshold: boxThreshold,
        text_threshold: textThreshold,
        show_visualisation: showVisualisation,
      },
    });

    const result = normalizeOutput(output);
    if (options.crop) {
      result.cropPaths = await cropDetections(imagePath, result.detections, options.crop);
    }
    return result;
  } finally {
    if (tempPath && fs.existsSync(tempPath)) {
      try {
        fs.unlinkSync(tempPath);
      } catch {
        /* ignore */
      }
    }
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage('Usage: $0 [options]')
    .option('url', {
      alias: 'u',
      type: 'string',
      description: 'Image URL (downloaded via shared utils/download, same as npm run download-file)',
    })
    .option('image', {
      alias: 'i',
      type: 'string',
      description: 'Local image file (alternative to --url)',
    })
    .option('query', {
      alias: 'q',
      type: 'string',
      description: 'Comma-separated labels / phrases to detect (e.g. "person, red car, dog")',
      demandOption: true,
    })
    .option('box-threshold', {
      type: 'number',
      description: 'Min box confidence (0–1, default 0.25)',
      default: 0.25,
    })
    .option('text-threshold', {
      type: 'number',
      description: 'Text/label match threshold (0–1, default 0.25)',
      default: 0.25,
    })
    .option('show-visualisation', {
      type: 'boolean',
      description: 'Return annotated result_image URL from the API',
      default: true,
    })
    .option('json', {
      type: 'boolean',
      description: 'Print JSON only (detections + optional result_image + cropPaths)',
      default: false,
    })
    .option('crop', {
      type: 'boolean',
      description: 'Save each bbox region as an image file (Sharp extract)',
      default: false,
    })
    .option('crop-label', {
      type: 'string',
      description:
        'Only save crops whose detection label contains this text (case-insensitive), e.g. "chair"',
    })
    .option('crop-dir', {
      type: 'string',
      description: 'Folder for crop images',
      default: 'downloads/grounding-dino-crops',
    })
    .option('crop-format', {
      type: 'string',
      choices: ['png', 'jpeg'] as const,
      description: 'Output format for crops',
      default: 'png' as const,
    })
    .example([
      [
        '$0 -u https://example.com/photo.jpg -q "face, laptop, coffee mug"',
        'Detect objects from a URL',
      ],
      ['$0 -i ./shot.png -q "stop sign, pedestrian"', 'Use a local image'],
      [
        '$0 -u https://example.com/p.jpg -q "chair, table, person" --crop --crop-label chair',
        'Save only chair regions to files',
      ],
    ])
    .help()
    .alias('help', 'h')
    .argv;

  const spinner = argv.json ? null : ora('Running Grounding DINO…').start();

  try {
    const crop =
      argv.crop || argv['crop-label']
        ? {
            labelFilter: argv['crop-label'],
            outputDir: argv['crop-dir'],
            format: argv['crop-format'] as 'png' | 'jpeg',
          }
        : undefined;

    const result = await detectObjects({
      url: argv.url,
      image: argv.image,
      query: argv.query,
      boxThreshold: argv['box-threshold'],
      textThreshold: argv['text-threshold'],
      showVisualisation: argv['show-visualisation'],
      json: argv.json,
      crop,
    });

    const cropNote =
      result.cropPaths && result.cropPaths.length > 0
        ? `, ${result.cropPaths.length} crop(s) saved`
        : '';
    spinner?.succeed(chalk.green(`Found ${result.detections.length} detection(s)${cropNote}`));

    if (argv.json) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      for (const d of result.detections) {
        console.log(
          chalk.cyan(`• ${d.label}`),
          chalk.gray(`conf=${d.confidence.toFixed(3)}`),
          chalk.gray(`bbox=[${d.bbox.join(', ')}]`),
        );
      }
      if (result.result_image) {
        console.log(chalk.gray('\nAnnotated preview:'), result.result_image);
      }
      if (result.cropPaths && result.cropPaths.length > 0) {
        console.log(chalk.gray('\nCrops:'));
        for (const p of result.cropPaths) {
          console.log(chalk.gray('  '), p);
        }
      } else if (argv.crop || argv['crop-label']) {
        console.log(
          chalk.yellow(
            '\nNo crop files written (no matching detections or empty boxes). Try a broader --query or lower thresholds.',
          ),
        );
      }
    }
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : 'Unknown error';
    if (argv.json) {
      console.error(JSON.stringify({ error: msg }));
    } else {
      spinner?.fail(chalk.red(msg));
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
