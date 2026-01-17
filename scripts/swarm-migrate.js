// Swarm Migration Script - Distribute migration tasks across team
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class SwarmMigrator {
  constructor() {
    this.components = [
      { name: 'Button', difficulty: 1, assignee: null, estimated: '5min', status: 'pending' },
      { name: 'Input', difficulty: 1, assignee: null, estimated: '5min', status: 'pending' },
      { name: 'Modal', difficulty: 2, assignee: null, estimated: '10min', status: 'pending' },
      { name: 'Form', difficulty: 3, assignee: null, estimated: '15min', status: 'pending' },
      { name: 'Table', difficulty: 3, assignee: null, estimated: '15min', status: 'pending' },
      { name: 'Chart', difficulty: 4, assignee: null, estimated: '20min', status: 'pending' },
      { name: 'Wizard', difficulty: 5, assignee: null, estimated: '30min', status: 'pending' },
      { name: 'Dashboard', difficulty: 5, assignee: null, estimated: '30min', status: 'pending' },
      { name: 'DataGrid', difficulty: 4, assignee: null, estimated: '25min', status: 'pending' },
      { name: 'FileUpload', difficulty: 3, assignee: null, estimated: '15min', status: 'pending' },
      {
        name: 'Notification',
        difficulty: 2,
        assignee: null,
        estimated: '10min',
        status: 'pending',
      },
      { name: 'Tooltip', difficulty: 1, assignee: null, estimated: '5min', status: 'pending' },
      { name: 'Dropdown', difficulty: 2, assignee: null, estimated: '10min', status: 'pending' },
      { name: 'Tabs', difficulty: 2, assignee: null, estimated: '10min', status: 'pending' },
      { name: 'Accordion', difficulty: 3, assignee: null, estimated: '15min', status: 'pending' },
      { name: 'Calendar', difficulty: 4, assignee: null, estimated: '20min', status: 'pending' },
    ];

    this.teamMembers = ['alice-dev', 'bob-dev', 'charlie-dev', 'diana-dev'];
  }

  assignTasks() {
    console.log('🐝 Starting swarm migration assignment...\n');

    // Sort components by difficulty (easiest first for round-robin)
    this.components.sort((a, b) => a.difficulty - b.difficulty);

    // Round-robin assignment
    this.teamMembers.forEach((member, index) => {
      const memberTasks = this.components.filter((_, i) => i % this.teamMembers.length === index);
      memberTasks.forEach((task) => {
        task.assignee = member;
        task.status = 'assigned';
      });
    });

    this.displayAssignments();
    this.generateScripts();
  }

  displayAssignments() {
    console.log('📋 Migration Task Assignments:\n');

    const assignments = {};
    this.teamMembers.forEach((member) => {
      assignments[member] = this.components.filter((c) => c.assignee === member);
    });

    this.teamMembers.forEach((member) => {
      const tasks = assignments[member];
      console.log(`👤 ${member}:`);
      tasks.forEach((task) => {
        console.log(`  • ${task.name} (${task.estimated}) - Difficulty: ${task.difficulty}`);
      });
      console.log(
        `  📊 Total: ${tasks.length} components, ~${this.calculateTotalTime(tasks)} minutes\n`
      );
    });
  }

  calculateTotalTime(tasks) {
    return tasks.reduce((total, task) => {
      const minutes = parseInt(task.estimated.replace('min', ''));
      return total + minutes;
    }, 0);
  }

  generateScripts() {
    console.log('📝 Generating individual migration scripts...\n');

    this.teamMembers.forEach((member) => {
      const memberTasks = this.components.filter((c) => c.assignee === member);
      this.generateMemberScript(member, memberTasks);
    });

    this.generateMasterScript();
  }

  generateMemberScript(member, tasks) {
    const scriptContent = `#!/bin/bash
# Migration script for ${member}
# Generated: ${new Date().toISOString()}

echo "🧑‍💻 Migration tasks for ${member}"
echo "📊 Assigned ${tasks.length} components"
echo "⏱️  Estimated time: ~${this.calculateTotalTime(tasks)} minutes"
echo "========================================"

${tasks
  .map(
    (task) => `
echo ""
echo "▶️  Migrating ${task.name} (${task.estimated})"
echo "   Difficulty: ${task.difficulty}/5"

# Run migration for this component
npm run migrate:single -- ${task.name}

# Mark as completed
echo "✅ ${task.name} migration completed"
`
  )
  .join('\n')}

echo ""
echo "🎉 All migrations completed for ${member}!"
echo "Please run 'npm test' to validate all changes."
`;

    const scriptPath = `scripts/migrate-${member}.sh`;
    fs.writeFileSync(scriptPath, scriptContent);
    execSync(`chmod +x ${scriptPath}`);

    console.log(`✅ Generated ${scriptPath}`);
  }

  generateMasterScript() {
    const scriptContent = `#!/bin/bash
# Master migration script - Run all team migrations
# Generated: ${new Date().toISOString()}

echo "🐝 Swarm Migration Master Script"
echo "================================="
echo "This will run migrations for all team members in parallel"
echo ""

# Create backup before starting
echo "📦 Creating backup..."
git checkout -b swarm-migration-$(date +%Y%m%d-%H%M%S)
git add .
git commit -m "Pre-swarm migration backup"

echo ""
echo "🚀 Starting parallel migrations..."

# Run all member scripts in parallel
${this.teamMembers.map((member) => `scripts/migrate-${member}.sh &`).join('\n')}

# Wait for all to complete
wait

echo ""
echo "🎊 All swarm migrations completed!"
echo "Please validate with: npm test"
`;

    const scriptPath = `scripts/swarm-migration-master.sh`;
    fs.writeFileSync(scriptPath, scriptContent);
    execSync(`chmod +x ${scriptPath}`);

    console.log(`✅ Generated ${scriptPath}`);
  }

  showStats() {
    const totalComponents = this.components.length;
    const totalTime = this.components.reduce(
      (sum, c) => sum + parseInt(c.estimated.replace('min', '')),
      0
    );
    const avgTimePerPerson = Math.ceil(totalTime / this.teamMembers.length);

    console.log('\n📊 Swarm Migration Statistics:');
    console.log(`   Total Components: ${totalComponents}`);
    console.log(`   Team Members: ${this.teamMembers.length}`);
    console.log(`   Total Time: ${totalTime} minutes`);
    console.log(`   Avg Time/Person: ${avgTimePerPerson} minutes`);
    console.log(`   Parallel Efficiency: ${Math.round((totalTime / avgTimePerPerson) * 100)}%`);
  }
}

// CLI interface
function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'assign';

  const swarm = new SwarmMigrator();

  switch (command) {
    case 'assign':
      swarm.assignTasks();
      swarm.showStats();
      break;
    case 'stats':
      swarm.showStats();
      break;
    default:
      console.log('Usage: node swarm-migrate.js [assign|stats]');
  }
}

// Export for use as module
module.exports = SwarmMigrator;

// Run if called directly
if (require.main === module) {
  main();
}
