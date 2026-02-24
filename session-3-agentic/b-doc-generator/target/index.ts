import express from 'express';
import { taskRouter } from './routes/tasks';
import { userRouter } from './routes/users';
import { connectDB } from './db';

const app = express();
app.use(express.json());

app.use('/api/tasks', taskRouter);
app.use('/api/users', userRouter);

app.get('/health', (_req, res) => res.json({ ok: true }));

connectDB().then(() => {
  app.listen(3000, () => console.log('Server on 3000'));
});

export default app;
