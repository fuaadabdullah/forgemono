#!/usr/bin/env bash
# Generate Datadog Dashboard JSON for Goblin Assistant Process Monitoring

cat << 'EOF' > goblin-assistant-processes-dashboard.json
{
  "title": "Goblin Assistant - Process Monitoring",
  "description": "Comprehensive process monitoring for Goblin Assistant backend",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.processes.cpu.pct{service:goblin-assistant} by {process}",
            "display_type": "line",
            "style": {
              "palette": "dog_classic",
              "line_type": "solid",
              "line_width": "normal"
            }
          }
        ],
        "title": "CPU Usage by Process (%)"
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.processes.mem.rss{service:goblin-assistant} by {process}",
            "display_type": "area",
            "style": {
              "palette": "dog_classic"
            }
          }
        ],
        "title": "Memory Usage (RSS) by Process"
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "sum:system.processes.io.read_bytes{service:goblin-assistant}.as_rate()",
            "display_type": "bars",
            "style": {
              "palette": "green"
            }
          },
          {
            "q": "sum:system.processes.io.write_bytes{service:goblin-assistant}.as_rate()",
            "display_type": "bars",
            "style": {
              "palette": "orange"
            }
          }
        ],
        "title": "I/O Operations (bytes/sec)"
      }
    },
    {
      "definition": {
        "type": "toplist",
        "requests": [
          {
            "q": "top(avg:system.processes.cpu.pct{service:goblin-assistant} by {process}, 10, 'mean', 'desc')"
          }
        ],
        "title": "Top 10 CPU Consumers"
      }
    },
    {
      "definition": {
        "type": "query_value",
        "requests": [
          {
            "q": "count_nonzero(avg:system.processes.number{service:goblin-assistant})"
          }
        ],
        "title": "Active Process Count"
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:system.processes.open_file_descriptors{service:goblin-assistant}",
            "display_type": "line"
          }
        ],
        "title": "Open File Descriptors"
      }
    }
  ],
  "template_variables": [
    {
      "name": "env",
      "default": "production",
      "prefix": "env"
    },
    {
      "name": "host",
      "default": "*",
      "prefix": "host"
    }
  ],
  "layout_type": "ordered",
  "notify_list": [],
  "tags": [
    "service:goblin-assistant",
    "component:backend"
  ]
}
EOF

echo "✓ Dashboard JSON generated: goblin-assistant-processes-dashboard.json"
echo ""
echo "Import to Datadog:"
echo "  1. Go to: https://app.datadoghq.com/dashboard/lists"
echo "  2. Click 'New Dashboard'"
echo "  3. Import the JSON file"
