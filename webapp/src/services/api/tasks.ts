import { TaskDTO, TaskStatus } from '../../common/types';
import client from './client';

export const getStudyRunningTasks = async (sid: string): Promise<Array<TaskDTO>> => {
  const res = await client.post('/v1/tasks', {
    // eslint-disable-next-line @typescript-eslint/camelcase
    ref_id: sid,
    type: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllRunningTasks = async (): Promise<Array<TaskDTO>> => {
  const res = await client.post('/v1/tasks', {
    type: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getTask = async (id: string, withLogs = false): Promise<TaskDTO> => {
  const res = await client.get(`/v1/tasks/${id}?with_logs=${withLogs}`);
  return res.data;
};

export default {};
