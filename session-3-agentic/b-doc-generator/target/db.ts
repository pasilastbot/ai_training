interface DBConnection {
  query: (sql: string, params?: unknown[]) => Promise<{ rows: unknown[] }>;
}

let connection: DBConnection | null = null;

export async function connectDB(): Promise<void> {
  connection = {
    query: async (sql: string, params?: unknown[]) => {
      console.log('Query:', sql, params);
      return { rows: [] };
    }
  };
}

export function getDB(): DBConnection {
  if (!connection) throw new Error('Database not connected');
  return connection;
}
