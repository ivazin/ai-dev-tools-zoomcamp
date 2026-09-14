import { IApiService, IRealtimeService } from '../types/services';
import { mockApiService, mockRealtimeService } from './mockService';
import { httpApiService, webSocketRealtimeService } from './httpService';

// Default to mock unless explicitly configured otherwise via environment variable
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false';

export interface ServiceContainer {
  api: IApiService;
  realtime: IRealtimeService;
  isMock: boolean;
}

export const services: ServiceContainer = {
  api: USE_MOCK ? mockApiService : httpApiService,
  realtime: USE_MOCK ? mockRealtimeService : webSocketRealtimeService,
  isMock: USE_MOCK,
};

export default services;
