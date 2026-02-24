import { Router } from 'express';
import { TaskService } from '../services/task-service';

export const taskRouter = Router();
const service = new TaskService();

taskRouter.get('/', async (_req, res) => {
  const tasks = await service.getAll();
  res.json({ data: tasks });
});

taskRouter.get('/:id', async (req, res) => {
  const task = await service.getById(req.params.id);
  if (!task) return res.status(404).json({ error: 'Not found' });
  res.json({ data: task });
});

taskRouter.post('/', async (req, res) => {
  const task = await service.create(req.body);
  res.status(201).json({ data: task });
});

taskRouter.patch('/:id', async (req, res) => {
  const task = await service.update(req.params.id, req.body);
  if (!task) return res.status(404).json({ error: 'Not found' });
  res.json({ data: task });
});

taskRouter.delete('/:id', async (req, res) => {
  await service.remove(req.params.id);
  res.status(204).send();
});
