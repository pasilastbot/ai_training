import { getDB } from '../db';

interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  assigneeId: string | null;
  createdAt: string;
}

export class TaskService {
  async getAll(): Promise<Task[]> {
    const db = getDB();
    const result = await db.query('SELECT * FROM tasks ORDER BY created_at DESC');
    return result.rows as Task[];
  }

  async getById(id: string): Promise<Task | null> {
    const db = getDB();
    const result = await db.query('SELECT * FROM tasks WHERE id = $1', [id]);
    return (result.rows[0] as Task) || null;
  }

  async create(data: Partial<Task>): Promise<Task> {
    const db = getDB();
    const result = await db.query(
      'INSERT INTO tasks (title, description, status, assignee_id) VALUES ($1, $2, $3, $4) RETURNING *',
      [data.title, data.description || '', data.status || 'todo', data.assigneeId || null]
    );
    return result.rows[0] as Task;
  }

  async update(id: string, data: Partial<Task>): Promise<Task | null> {
    const db = getDB();
    const fields: string[] = [];
    const values: unknown[] = [];
    let idx = 1;

    if (data.title) { fields.push(`title = $${idx++}`); values.push(data.title); }
    if (data.description) { fields.push(`description = $${idx++}`); values.push(data.description); }
    if (data.status) { fields.push(`status = $${idx++}`); values.push(data.status); }
    if (data.assigneeId !== undefined) { fields.push(`assignee_id = $${idx++}`); values.push(data.assigneeId); }

    if (fields.length === 0) return this.getById(id);

    values.push(id);
    const result = await db.query(
      `UPDATE tasks SET ${fields.join(', ')} WHERE id = $${idx} RETURNING *`,
      values
    );
    return (result.rows[0] as Task) || null;
  }

  async remove(id: string): Promise<void> {
    const db = getDB();
    await db.query('DELETE FROM tasks WHERE id = $1', [id]);
  }
}
