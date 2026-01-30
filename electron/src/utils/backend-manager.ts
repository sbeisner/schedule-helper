import { ChildProcess, spawn } from 'child_process';
import * as path from 'path';
import * as http from 'http';

interface BackendManagerOptions {
  isDev: boolean;
  port: number;
}

export class BackendManager {
  private process: ChildProcess | null = null;
  private options: BackendManagerOptions;
  private running = false;

  constructor(options: BackendManagerOptions) {
    this.options = options;
  }

  async start(): Promise<void> {
    if (this.running) {
      console.log('Backend already running');
      return;
    }

    const { isDev, port } = this.options;

    let pythonPath: string;
    let backendPath: string;

    if (isDev) {
      // Development: use system Python and local backend directory
      pythonPath = 'python3';
      backendPath = path.join(__dirname, '..', '..', '..', 'backend');
    } else {
      // Production: use bundled Python and backend from resources
      // Note: For full production, you'd bundle Python or use pyinstaller
      pythonPath = 'python3';
      backendPath = path.join(process.resourcesPath, 'backend');
    }

    const args = [
      '-m',
      'uvicorn',
      'app.main:app',
      '--host',
      '127.0.0.1',
      '--port',
      port.toString(),
    ];

    if (isDev) {
      args.push('--reload');
    }

    console.log(`Starting backend: ${pythonPath} ${args.join(' ')}`);
    console.log(`Working directory: ${backendPath}`);

    this.process = spawn(pythonPath, args, {
      cwd: backendPath,
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1',
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    this.process.stdout?.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });

    this.process.stderr?.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });

    this.process.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
      this.running = false;
      this.process = null;
    });

    this.process.on('error', (err) => {
      console.error('Failed to start backend:', err);
      this.running = false;
    });

    // Wait for backend to be ready
    await this.waitForReady(port);
    this.running = true;
  }

  async stop(): Promise<void> {
    if (!this.process) {
      return;
    }

    console.log('Stopping backend...');

    return new Promise((resolve) => {
      if (!this.process) {
        resolve();
        return;
      }

      this.process.on('close', () => {
        this.running = false;
        this.process = null;
        console.log('Backend stopped');
        resolve();
      });

      // Try graceful shutdown first
      this.process.kill('SIGTERM');

      // Force kill after 5 seconds
      setTimeout(() => {
        if (this.process) {
          this.process.kill('SIGKILL');
        }
      }, 5000);
    });
  }

  isRunning(): boolean {
    return this.running;
  }

  private async waitForReady(port: number, timeout = 30000): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      try {
        await this.healthCheck(port);
        console.log('Backend is ready');
        return;
      } catch {
        // Not ready yet, wait and retry
        await this.sleep(500);
      }
    }

    throw new Error(`Backend did not start within ${timeout}ms`);
  }

  private healthCheck(port: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port,
          path: '/health',
          method: 'GET',
          timeout: 2000,
        },
        (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            reject(new Error(`Health check failed: ${res.statusCode}`));
          }
        }
      );

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Health check timeout'));
      });

      req.end();
    });
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
