import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { BackendManager } from './utils/backend-manager';

let mainWindow: BrowserWindow | null = null;
let backendManager: BackendManager | null = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

async function createWindow(): Promise<void> {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hiddenInset',
    show: false,
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Load the app
  if (isDev) {
    // In development, load from Angular dev server
    await mainWindow.loadURL('http://localhost:4200');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built Angular app
    const frontendPath = path.join(
      process.resourcesPath,
      'frontend',
      'schedule-manager',
      'browser',
      'index.html'
    );
    await mainWindow.loadFile(frontendPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function startBackend(): Promise<void> {
  backendManager = new BackendManager({
    isDev,
    port: 8765,
  });

  try {
    await backendManager.start();
    console.log('Backend started successfully');
  } catch (error) {
    console.error('Failed to start backend:', error);
    app.quit();
  }
}

async function stopBackend(): Promise<void> {
  if (backendManager) {
    await backendManager.stop();
    backendManager = null;
  }
}

// App lifecycle
app.whenReady().then(async () => {
  // Start backend first
  await startBackend();

  // Then create window
  await createWindow();

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on('window-all-closed', async () => {
  await stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async () => {
  await stopBackend();
});

// IPC handlers
ipcMain.handle('backend:status', () => {
  return backendManager?.isRunning() ?? false;
});

ipcMain.handle('backend:restart', async () => {
  await stopBackend();
  await startBackend();
  return true;
});

ipcMain.handle('app:version', () => {
  return app.getVersion();
});
