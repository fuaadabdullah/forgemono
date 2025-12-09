#!/bin/bash
# CI/CD Performance Monitoring Script
# Tracks script execution times and CI/CD pipeline performance
# Usage: ./monitor_ci_performance.sh [--ci] [--report]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/.ci-monitoring"
LOG_FILE="${LOG_DIR}/performance.log"

# Parse command line arguments
CI_MODE=false
GENERATE_REPORT=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --ci)
      CI_MODE=true
      shift
      ;;
    --report)
      GENERATE_REPORT=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--ci] [--report]"
      exit 1
      ;;
  esac
done

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log performance metrics
log_performance() {
  local script_name="$1"
  local start_time="$2"
  local end_time="$3"
  local exit_code="$4"

  local duration=$((end_time - start_time))
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

  echo "${timestamp}|${script_name}|${duration}|${exit_code}" >> "$LOG_FILE"
}

# Function to generate performance report
generate_report() {
  if [ ! -f "$LOG_FILE" ]; then
    echo "No performance data available yet."
    return
  fi

  echo "📊 CI/CD Performance Report"
  echo "=========================="
  echo ""

  echo "Recent Script Executions:"
  tail -10 "$LOG_FILE" | while IFS='|' read -r timestamp script duration exit_code; do
    status="✅"
    [ "$exit_code" != "0" ] && status="❌"
    printf "%s | %s | %ss | %s\n" "$timestamp" "$script" "$duration" "$status"
  done

  echo ""
  echo "Average Execution Times:"
  awk -F'|' '
    { script_times[$2] += $3; script_count[$2]++ }
    END {
      for (script in script_times) {
        avg = script_times[script] / script_count[script]
        printf "%s: %.2fs (n=%d)\n", script, avg, script_count[script]
      }
    }
  ' "$LOG_FILE" | sort -t: -k2 -n

  echo ""
  echo "Failure Rate by Script:"
  awk -F'|' '
    { script_total[$2]++; if ($4 != "0") script_failures[$2]++ }
    END {
      for (script in script_total) {
        failure_rate = (script_failures[script] / script_total[script]) * 100
        printf "%s: %.1f%% (%d/%d)\n", script, failure_rate, script_failures[script], script_total[script]
      }
    }
  ' "$LOG_FILE" | sort -t: -k2 -nr
}

# If report requested, generate and exit
if [ "$GENERATE_REPORT" = true ]; then
  generate_report
  exit 0
fi

# Main monitoring logic
if [ "$CI_MODE" = true ]; then
  echo "🤖 CI Performance Monitor Active"

  # This script would be called by CI/CD to track performance
  # Individual scripts would call this to log their execution times

  # Example usage in other scripts:
  # start_time=$(date +%s)
  # # ... script logic ...
  # end_time=$(date +%s)
  # bash scripts/monitoring/monitor_ci_performance.sh --log "$0" "$start_time" "$end_time" "$?"

else
  # Interactive mode - show current status
  echo "🔍 CI/CD Performance Monitor"
  echo "Log file: $LOG_FILE"

  if [ -f "$LOG_FILE" ]; then
    echo ""
    generate_report
  else
    echo "No performance data collected yet."
    echo "Run scripts with CI monitoring to start collecting data."
  fi
fi
