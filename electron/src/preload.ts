import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Backend management
  getBackendStatus: () => ipcRenderer.invoke('backend:status'),
  restartBackend: () => ipcRenderer.invoke('backend:restart'),

  // App info
  getAppVersion: () => ipcRenderer.invoke('app:version'),

  // Platform info
  platform: process.platform,
  isDev: process.env.NODE_ENV === 'development',
});

// Type definitions for TypeScript
declare global {
  interface Window {
    electronAPI: {
      getBackendStatus: () => Promise<boolean>;
      restartBackend: () => Promise<boolean>;
      getAppVersion: () => Promise<string>;
      platform: NodeJS.Platform;
      isDev: boolean;
    };
  }
}
