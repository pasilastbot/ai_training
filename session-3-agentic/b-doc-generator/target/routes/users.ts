import { Router } from 'express';
import { UserService } from '../services/user-service';

export const userRouter = Router();
const service = new UserService();

userRouter.get('/', async (_req, res) => {
  const users = await service.getAll();
  res.json({ data: users });
});

userRouter.get('/:id', async (req, res) => {
  const user = await service.getById(req.params.id);
  if (!user) return res.status(404).json({ error: 'Not found' });
  res.json({ data: user });
});

userRouter.post('/', async (req, res) => {
  const user = await service.create(req.body);
  res.status(201).json({ data: user });
});
