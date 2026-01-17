// Live Migration Dashboard with WebSocket Real-time Collaboration
const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

class LiveMigrationDashboard {
  constructor(port = 8080) {
    this.port = port;
    this.server = null;
    this.wss = null;
    this.migrationStatus = {
      total: 0,
      completed: 0,
      inProgress: [],
      teamProgress: {},
      startTime: Date.now(),
      lastUpdate: Date.now(),
    };

    this.scanInterval = null;
  }

  start() {
    console.log('🚀 Starting Live Migration Dashboard...');

    // Create HTTP server for serving the web interface
    this.server = http.createServer(this.handleHttpRequest.bind(this));
    this.wss = new WebSocket.Server({ server: this.server });

    // WebSocket connection handling
    this.wss.on('connection', this.handleWebSocketConnection.bind(this));

    // Start the server
    this.server.listen(this.port, () => {
      console.log(`📊 Dashboard available at: http://localhost:${this.port}`);
      console.log(`🔌 WebSocket endpoint: ws://localhost:${this.port}`);
      console.log('📱 Open the URL above in your browser to see real-time progress');
    });

    // Start periodic scanning
    this.startPeriodicScan();

    // Handle graceful shutdown
    process.on('SIGINT', this.stop.bind(this));
    process.on('SIGTERM', this.stop.bind(this));
  }

  handleHttpRequest(req, res) {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;

    if (pathname === '/') {
      // Serve the main dashboard HTML
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(this.generateDashboardHTML());
    } else if (pathname === '/api/status') {
      // Serve JSON API for current status
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(this.migrationStatus));
    } else if (pathname === '/api/scan') {
      // Trigger manual scan
      this.scanProject();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'scan_triggered' }));
    } else {
      res.writeHead(404);
      res.end('Not Found');
    }
  }

  handleWebSocketConnection(ws) {
    console.log('🔌 New WebSocket connection established');

    // Send current status to new client
    ws.send(
      JSON.stringify({
        type: 'status',
        data: this.migrationStatus,
      })
    );

    // Handle messages from clients
    ws.on('message', (message) => {
      try {
        const { type, data } = JSON.parse(message.toString());

        switch (type) {
          case 'start_migration':
            this.handleMigrationStart(data);
            break;
          case 'complete_migration':
            this.handleMigrationComplete(data);
            break;
          case 'update_progress':
            this.handleProgressUpdate(data);
            break;
          case 'ping':
            ws.send(JSON.stringify({ type: 'pong' }));
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    ws.on('close', () => {
      console.log('🔌 WebSocket connection closed');
    });
  }

  handleMigrationStart(data) {
    const { component, developer } = data;
    this.migrationStatus.inProgress.push({ component, developer, startTime: Date.now() });

    if (developer) {
      if (!this.migrationStatus.teamProgress[developer]) {
        this.migrationStatus.teamProgress[developer] = { completed: 0, inProgress: 0 };
      }
      this.migrationStatus.teamProgress[developer].inProgress++;
    }

    this.broadcastUpdate();
  }

  handleMigrationComplete(data) {
    const { component, developer } = data;

    // Remove from in-progress
    this.migrationStatus.inProgress = this.migrationStatus.inProgress.filter(
      (item) => !(item.component === component && item.developer === developer)
    );

    // Update completed count
    this.migrationStatus.completed++;

    // Update team progress
    if (developer && this.migrationStatus.teamProgress[developer]) {
      this.migrationStatus.teamProgress[developer].inProgress--;
      this.migrationStatus.teamProgress[developer].completed++;
    }

    this.broadcastUpdate();
  }

  handleProgressUpdate(data) {
    // Update migration status with new data
    Object.assign(this.migrationStatus, data);
    this.migrationStatus.lastUpdate = Date.now();
    this.broadcastUpdate();
  }

  broadcastUpdate() {
    const message = JSON.stringify({
      type: 'status',
      data: this.migrationStatus,
    });

    this.wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  startPeriodicScan() {
    // Scan every 30 seconds
    this.scanInterval = setInterval(() => {
      this.scanProject();
    }, 30000);

    // Initial scan
    this.scanProject();
  }

  scanProject() {
    try {
      const testFiles = this.findTestFiles(process.cwd());
      const migratedCount = this.countMigratedTests(testFiles);

      this.migrationStatus.total = testFiles.length;
      this.migrationStatus.completed = migratedCount;
      this.migrationStatus.lastUpdate = Date.now();

      this.broadcastUpdate();
    } catch (error) {
      console.error('Error scanning project:', error);
    }
  }

  findTestFiles(rootDir) {
    const testFiles = [];

    function scan(dir) {
      try {
        const items = fs.readdirSync(dir);

        items.forEach((item) => {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);

          if (stat.isDirectory() && !this.shouldSkipDir(item)) {
            scan.call(this, fullPath);
          } else if (stat.isFile() && this.isTestFile(item)) {
            testFiles.push(fullPath);
          }
        });
      } catch (error) {
        // Skip directories we can't read
      }
    }

    scan.call(this, rootDir);
    return testFiles;
  }

  shouldSkipDir(dirName) {
    const skipDirs = ['node_modules', '.git', 'dist', 'build', 'coverage'];
    return skipDirs.includes(dirName) || dirName.startsWith('.');
  }

  isTestFile(fileName) {
    return /\.(test|spec)\.(js|jsx|ts|tsx)$/.test(fileName);
  }

  countMigratedTests(testFiles) {
    let migrated = 0;

    testFiles.forEach((file) => {
      try {
        const content = fs.readFileSync(file, 'utf-8');
        if (this.isMigrated(content)) {
          migrated++;
        }
      } catch (error) {
        // Skip files we can't read
      }
    });

    return migrated;
  }

  isMigrated(content) {
    // Check for Testing Library usage (migrated) vs Enzyme usage (not migrated)
    const hasTestingLibrary = /from ['"]@testing-library\/react['"]/.test(content);
    const hasEnzyme = /from ['"]enzyme['"]/.test(content);

    return hasTestingLibrary && !hasEnzyme;
  }

  generateDashboardHTML() {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Live Migration Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #2563eb;
            margin-bottom: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 5px;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
        }

        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981, #2563eb);
            transition: width 0.3s ease;
        }

        .team-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .team-member {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }

        .team-member:last-child {
            border-bottom: none;
        }

        .activity-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .activity-item {
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
        }

        .activity-item:last-child {
            border-bottom: none;
        }

        .activity-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-right: 10px;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }

        .status-online { background: #10b981; }
        .status-busy { background: #f59e0b; }
        .status-offline { background: #6b7280; }

        .controls {
            text-align: center;
            margin-top: 20px;
        }

        button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
        }

        button:hover {
            background: #1d4ed8;
        }

        .last-update {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Live Migration Dashboard</h1>
            <p>Real-time Enzyme to Testing Library migration progress</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-tests">0</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="completed-tests">0</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="progress-percent">0%</div>
                <div class="stat-label">Progress</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="active-devs">0</div>
                <div class="stat-label">Active Developers</div>
            </div>
        </div>

        <div class="progress-bar">
            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
        </div>

        <div class="team-section">
            <h2>👥 Team Progress</h2>
            <div id="team-progress">
                <p>No team activity yet</p>
            </div>
        </div>

        <div class="activity-section">
            <h2>📋 Current Activity</h2>
            <div id="current-activity">
                <p>No active migrations</p>
            </div>
        </div>

        <div class="controls">
            <button onclick="scanNow()">🔄 Scan Now</button>
            <button onclick="startMigration()">▶️ Start Migration</button>
            <button onclick="completeMigration()">✅ Complete Migration</button>
        </div>

        <div class="last-update" id="last-update">
            Last updated: Never
        </div>
    </div>

    <script>
        let ws;
        let currentStatus = {
            total: 0,
            completed: 0,
            inProgress: [],
            teamProgress: {}
        };

        function connectWebSocket() {
            ws = new WebSocket('ws://localhost:${this.port}');

            ws.onopen = function() {
                console.log('Connected to dashboard');
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'status') {
                    updateDashboard(message.data);
                }
            };

            ws.onclose = function() {
                console.log('Disconnected from dashboard');
                setTimeout(connectWebSocket, 1000);
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        function updateDashboard(status) {
            currentStatus = status;

            // Update stats
            document.getElementById('total-tests').textContent = status.total;
            document.getElementById('completed-tests').textContent = status.completed;
            const progressPercent = status.total > 0 ? Math.round((status.completed / status.total) * 100) : 0;
            document.getElementById('progress-percent').textContent = progressPercent + '%';

            // Update progress bar
            document.getElementById('progress-fill').style.width = progressPercent + '%';

            // Update active developers
            const activeDevs = Object.keys(status.teamProgress).length;
            document.getElementById('active-devs').textContent = activeDevs;

            // Update team progress
            updateTeamProgress(status.teamProgress);

            // Update current activity
            updateCurrentActivity(status.inProgress);

            // Update last update time
            const lastUpdate = new Date(status.lastUpdate || Date.now());
            document.getElementById('last-update').textContent =
                'Last updated: ' + lastUpdate.toLocaleTimeString();
        }

        function updateTeamProgress(teamProgress) {
            const container = document.getElementById('team-progress');

            if (Object.keys(teamProgress).length === 0) {
                container.innerHTML = '<p>No team activity yet</p>';
                return;
            }

            let html = '';
            Object.entries(teamProgress).forEach(([developer, progress]) => {
                const total = progress.completed + progress.inProgress;
                const statusClass = progress.inProgress > 0 ? 'status-busy' : 'status-online';
                html += \`
                    <div class="team-member">
                        <span><span class="status-indicator \${statusClass}"></span>\${developer}</span>
                        <span>\${progress.completed} completed, \${progress.inProgress} in progress</span>
                    </div>
                \`;
            });

            container.innerHTML = html;
        }

        function updateCurrentActivity(inProgress) {
            const container = document.getElementById('current-activity');

            if (inProgress.length === 0) {
                container.innerHTML = '<p>No active migrations</p>';
                return;
            }

            let html = '';
            inProgress.forEach(item => {
                const startTime = new Date(item.startTime);
                const elapsed = Math.floor((Date.now() - startTime) / 1000 / 60); // minutes
                html += \`
                    <div class="activity-item">
                        <span class="activity-dot"></span>
                        <strong>\${item.developer || 'Unknown'}</strong> working on
                        <code>\${item.component}</code> (\${elapsed}m elapsed)
                    </div>
                \`;
            });

            container.innerHTML = html;
        }

        function scanNow() {
            fetch('/api/scan')
                .then(response => response.json())
                .then(data => console.log('Scan triggered:', data))
                .catch(error => console.error('Scan error:', error));
        }

        function startMigration() {
            const component = prompt('Enter component name:');
            const developer = prompt('Enter your name:');

            if (component && developer) {
                ws.send(JSON.stringify({
                    type: 'start_migration',
                    data: { component, developer }
                }));
            }
        }

        function completeMigration() {
            const component = prompt('Enter completed component name:');
            const developer = prompt('Enter your name:');

            if (component && developer) {
                ws.send(JSON.stringify({
                    type: 'complete_migration',
                    data: { component, developer }
                }));
            }
        }

        // Connect on page load
        connectWebSocket();

        // Periodic ping to keep connection alive
        setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    </script>
</body>
</html>`;
  }

  stop() {
    console.log('\n🛑 Stopping Live Migration Dashboard...');

    if (this.scanInterval) {
      clearInterval(this.scanInterval);
    }

    if (this.wss) {
      this.wss.close();
    }

    if (this.server) {
      this.server.close(() => {
        console.log('✅ Dashboard stopped');
        process.exit(0);
      });
    }
  }
}

// CLI interface
function main() {
  const args = process.argv.slice(2);
  const port = args[0] ? parseInt(args[0]) : 8080;

  const dashboard = new LiveMigrationDashboard(port);

  // Handle graceful shutdown
  process.on('SIGINT', () => dashboard.stop());
  process.on('SIGTERM', () => dashboard.stop());

  dashboard.start();
}

// Export for use as module
module.exports = LiveMigrationDashboard;

// Run if called directly
if (require.main === module) {
  main();
}
