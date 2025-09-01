#!/usr/bin/env node

import { Command } from "commander";

const program = new Command();

interface DateTimeOptions {
  format?: string;
  timezone?: string;
  utc?: boolean;
  timestamp?: boolean;
  locale?: string;
}

function getCurrentDateTime(options: DateTimeOptions): string {
  const now = new Date();
  
  // If timestamp requested, return Unix timestamp
  if (options.timestamp) {
    return now.getTime().toString();
  }
  
  // If UTC requested, use UTC methods
  if (options.utc) {
    return now.toUTCString();
  }
  
  // If timezone specified, use toLocaleString with timezone
  if (options.timezone) {
    const locale = options.locale || 'en-US';
    return now.toLocaleString(locale, {
      timeZone: options.timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  }
  
  // Handle custom format
  if (options.format) {
    const locale = options.locale || 'en-US';
    
    switch (options.format.toLowerCase()) {
      case 'iso':
        return now.toISOString();
      case 'date':
        return now.toLocaleDateString(locale);
      case 'time':
        return now.toLocaleTimeString(locale);
      case 'full':
        return now.toLocaleString(locale, {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      case 'short':
        return now.toLocaleString(locale, {
          year: '2-digit',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      case 'compact':
        return now.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z/, '');
      default:
        // Try to use the format string directly
        return now.toLocaleString(locale);
    }
  }
  
  // Default: human-readable format
  const locale = options.locale || 'en-US';
  return now.toLocaleString(locale, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

program
  .name("datetime")
  .description("Get current date and time in various formats")
  .version("1.0.0");

program
  .option("-f, --format <format>", "Output format: iso, date, time, full, short, compact, or custom")
  .option("-t, --timezone <timezone>", "Timezone (e.g., America/New_York, Europe/London, Asia/Tokyo)")
  .option("-u, --utc", "Show UTC time")
  .option("-s, --timestamp", "Show Unix timestamp (milliseconds)")
  .option("-l, --locale <locale>", "Locale for formatting (e.g., en-US, fi-FI, sv-SE)", "en-US")
  .action((options: DateTimeOptions) => {
    try {
      const result = getCurrentDateTime(options);
      console.log(result);
      console.log(`📅 Current date/time: ${result}`);
    } catch (error) {
      console.error("❌ Error getting date/time:", error);
      process.exit(1);
    }
  });

// Add examples to help
program.addHelpText('after', `
Examples:
  $ npm run datetime                           # Default: full human-readable format
  $ npm run datetime -- --format iso          # ISO 8601 format (2024-08-29T14:30:45.123Z)
  $ npm run datetime -- --format date         # Date only (8/29/2024)
  $ npm run datetime -- --format time         # Time only (2:30:45 PM)
  $ npm run datetime -- --format compact      # Compact format (20240829T143045)
  $ npm run datetime -- --timezone Europe/Helsinki  # Helsinki timezone
  $ npm run datetime -- --utc                 # UTC time
  $ npm run datetime -- --timestamp           # Unix timestamp
  $ npm run datetime -- --locale fi-FI        # Finnish locale formatting
  $ npm run datetime -- --timezone Asia/Tokyo --locale ja-JP  # Tokyo time in Japanese format
`);

program.parse();

