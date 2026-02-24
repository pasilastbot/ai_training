import { getDB } from '../db';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'member';
  createdAt: string;
}

export class UserService {
  async getAll(): Promise<User[]> {
    const db = getDB();
    const result = await db.query('SELECT * FROM users ORDER BY name');
    return result.rows as User[];
  }

  async getById(id: string): Promise<User | null> {
    const db = getDB();
    const result = await db.query('SELECT * FROM users WHERE id = $1', [id]);
    return (result.rows[0] as User) || null;
  }

  async create(data: Partial<User>): Promise<User> {
    const db = getDB();
    const result = await db.query(
      'INSERT INTO users (name, email, role) VALUES ($1, $2, $3) RETURNING *',
      [data.name, data.email, data.role || 'member']
    );
    return result.rows[0] as User;
  }

  async getByEmail(email: string): Promise<User | null> {
    const db = getDB();
    const result = await db.query('SELECT * FROM users WHERE email = $1', [email]);
    return (result.rows[0] as User) || null;
  }
}
