#!/usr/bin/env node

import { GoogleGenAI } from "@google/genai";
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

interface GoogleSearchOptions {
  query: string;
  model?: string;
  maxResults?: number;
  showSources?: boolean;
  format?: 'text' | 'json';
}

async function performGoogleSearch(options: GoogleSearchOptions): Promise<void> {
  try {
    // Initialize Google GenAI with API key
    const ai = new GoogleGenAI({ apiKey: API_KEY });

    console.log("🔍 Performing Google search with Gemini...");
    console.log(`Query: ${options.query}`);
    console.log(`Model: ${options.model || 'gemini-2.5-flash-lite'}`);

    // Create search prompt
    const searchPrompt = `Search for information about: ${options.query}

Please provide a comprehensive answer based on the most current and accurate information available through Google Search.`;

    // Configure with Google Search grounding
    const response = await ai.models.generateContent({
      model: options.model || "gemini-2.5-flash-lite",
      contents: searchPrompt,
      config: {
        tools: [{ googleSearch: {}, url_context: {}}], // Enable Google Search grounding
      },
    });

    if (!response.candidates || response.candidates.length === 0) {
      throw new Error("No candidates returned from Gemini API");
    }

    const candidate = response.candidates[0];
    if (!candidate.content || !candidate.content.parts) {
      throw new Error("No content parts returned from Gemini API");
    }

    // Extract and display the response
    const textParts = candidate.content.parts
      .filter(part => part.text)
      .map(part => part.text);

    if (options.format === 'json') {
      const result: {
        query: string;
        answer: string;
        sources: Array<{title: string; url: string}>;
        timestamp: string;
      } = {
        query: options.query,
        answer: textParts.join('\n'),
        sources: [],
        timestamp: new Date().toISOString()
      };

      // Extract sources if available
      if (response.candidates[0].groundingMetadata?.groundingChunks) {
        result.sources = response.candidates[0].groundingMetadata.groundingChunks
          .map(chunk => ({
            title: chunk.web?.title || 'Unknown',
            url: chunk.web?.uri || 'Unknown',
          }))
          .slice(0, options.maxResults || 10);
      }

      console.log(JSON.stringify(result, null, 2));
    } else {
      // Text format
      if (textParts.length > 0) {
        console.log("\n📄 Search Results:");
        console.log("=" .repeat(50));
        console.log(textParts.join('\n'));
      }

      // Show sources if requested
      if (options.showSources && response.candidates[0].groundingMetadata?.groundingChunks) {
        console.log("\n🔗 Sources:");
        console.log("-".repeat(30));
        
        const sources = response.candidates[0].groundingMetadata.groundingChunks
          .slice(0, options.maxResults || 10);
          
        sources.forEach((chunk, index) => {
          const title = chunk.web?.title || 'Unknown Title';
          const url = chunk.web?.uri || 'Unknown URL';
          console.log(`[${index + 1}] ${title}`);
          console.log(`    ${url}`);
        });
      }
    }

    console.log("\n✅ Google search completed!");

  } catch (error) {
    console.error("❌ Error performing Google search:", error);
    process.exit(1);
  }
}

// Set up CLI
program
  .name("google-search")
  .description("Perform Google search using Gemini's grounded search capability")
  .version("1.0.0");

program
  .requiredOption("-q, --query <query>", "Search query")
  .option("-m, --model <model>", "Gemini model to use", "gemini-2.5-flash")
  .option("-n, --max-results <number>", "Maximum number of sources to show", "10")
  .option("-s, --show-sources", "Show source URLs and titles", false)
  .option("-f, --format <format>", "Output format: 'text' or 'json'", "text")
  .action(async (options) => {
    await performGoogleSearch({
      query: options.query,
      model: options.model,
      maxResults: parseInt(options.maxResults),
      showSources: options.showSources,
      format: options.format as 'text' | 'json',
    });
  });

// Parse command line arguments
program.parse();
