#!/usr/bin/env node

import { GoogleGenAI } from "@google/genai";
import * as fs from "node:fs";
import * as path from "node:path";
import { program } from "commander";
import dotenv from "dotenv";

// Load environment variables
dotenv.config({ path: '.env.local' });

const API_KEY = process.env.GOOGLE_AI_STUDIO_KEY || process.env.GEMINI_API_KEY;

if (!API_KEY) {
  console.error('❌ Error: GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY environment variable is not set');
  console.error('Please set one of these environment variables in your .env.local file');
  process.exit(1);
}

interface NanoBananaOptions {
  prompt: string;
  output?: string;
  folder?: string;
  inputImage?: string;
  mode?: 'generate' | 'edit';
}

async function generateNanoBananaImage(options: NanoBananaOptions): Promise<void> {
  try {
    // Initialize Google GenAI with API key
    const ai = new GoogleGenAI({ apiKey: API_KEY });

    const isEditMode = options.mode === 'edit' || options.inputImage;
    
    if (isEditMode) {
      console.log("🍌 Editing image with nano-banana theme using Gemini...");
      
      // Validate input image exists
      if (!options.inputImage) {
        throw new Error("Input image path is required for editing mode");
      }
      
      if (!fs.existsSync(options.inputImage)) {
        throw new Error(`Input image file not found: ${options.inputImage}`);
      }
      
      console.log(`Input image: ${options.inputImage}`);
    } else {
      console.log("🍌 Generating nano-banana image with Gemini...");
    }
    
    console.log(`Prompt: ${options.prompt}`);

    // Prepare content for API call
    let contents: any;
    
    if (isEditMode && options.inputImage) {
      // Read and encode the input image
      const imageData = fs.readFileSync(options.inputImage);
      const base64Image = imageData.toString("base64");
      
      // Determine MIME type based on file extension
      const ext = path.extname(options.inputImage).toLowerCase();
      let mimeType = "image/png";
      if (ext === ".jpg" || ext === ".jpeg") {
        mimeType = "image/jpeg";
      } else if (ext === ".webp") {
        mimeType = "image/webp";
      }
      
      // Create prompt with image for editing
      contents = [
        { text: options.prompt },
        {
          inlineData: {
            mimeType: mimeType,
            data: base64Image,
          },
        },
      ];
    } else {
      // Simple text prompt for generation
      contents = options.prompt;
    }

    // Generate/edit image using gemini-2.5-flash-image-preview
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash-image-preview",
      contents: contents,
    });

    if (!response.candidates || response.candidates.length === 0) {
      throw new Error("No candidates returned from Gemini API");
    }

    const candidate = response.candidates[0];
    if (!candidate.content || !candidate.content.parts) {
      throw new Error("No content parts returned from Gemini API");
    }

    let imageGenerated = false;
    
    for (const part of candidate.content.parts) {
      if (part.text) {
        console.log("Generated description:", part.text);
      } else if (part.inlineData) {
        const imageData = part.inlineData.data;
        const buffer = Buffer.from(imageData, "base64");
        
        // Determine output path
        const outputFolder = options.folder || "public/images";
        const defaultFilename = isEditMode ? "nano-banana-edited.png" : "nano-banana-generated.png";
        const outputFilename = options.output || defaultFilename;
        
        // Ensure output directory exists
        if (!fs.existsSync(outputFolder)) {
          fs.mkdirSync(outputFolder, { recursive: true });
        }
        
        const outputPath = path.join(outputFolder, outputFilename);
        
        // Save the image
        fs.writeFileSync(outputPath, buffer);
        console.log(`🎨 Image saved as ${outputPath}`);
        imageGenerated = true;
      }
    }

    if (!imageGenerated) {
      throw new Error("No image data received from Gemini API");
    }

    const actionText = isEditMode ? "editing" : "generation";
    console.log(`✅ Nano-banana image ${actionText} completed!`);

  } catch (error) {
    const actionText = isEditMode ? "editing" : "generating";
    console.error(`❌ Error ${actionText} nano-banana image:`, error);
    process.exit(1);
  }
}

// Set up CLI
program
  .name("nano-banana")
  .description("Generate or edit images using Gemini 2.5 Flash Image Preview model")
  .version("1.0.0");

program
  .requiredOption("-p, --prompt <prompt>", "Text prompt for image generation or editing")
  .option("-i, --input-image <path>", "Path to input image for editing (enables edit mode)")
  .option("-o, --output <filename>", "Output filename (default: nano-banana-generated.png or nano-banana-edited.png)")
  .option("-f, --folder <folder>", "Output folder path (default: public/images)")
  .option("-m, --mode <mode>", "Mode: 'generate' or 'edit' (auto-detected if --input-image is provided)", "generate")
  .action(async (options) => {
    await generateNanoBananaImage({
      prompt: options.prompt,
      output: options.output,
      folder: options.folder,
      inputImage: options.inputImage,
      mode: options.inputImage ? 'edit' : options.mode as 'generate' | 'edit',
    });
  });

// Parse command line arguments
program.parse();
