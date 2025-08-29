import fs from 'fs';
import path from 'path';
import axios from 'axios';

export async function downloadFile(url: string, outputPath: string): Promise<void> {
  // Ensure directory exists
  const dir = path.dirname(outputPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  const response = await axios.get(url, { responseType: 'stream' });
  const writer = fs.createWriteStream(outputPath);

  return new Promise((resolve, reject) => {
    response.data.pipe(writer);
    let error: Error | null = null;

    writer.on('error', err => {
      error = err;
      writer.close();
      reject(err);
    });

    writer.on('close', () => {
      if (!error) {
        resolve();
      }
    });
  });
}
