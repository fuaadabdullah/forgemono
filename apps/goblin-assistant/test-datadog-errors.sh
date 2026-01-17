#!/bin/bash

# Datadog Error Tracking Test Script
# This script tests various error scenarios to verify Datadog RUM error tracking

echo "🧪 Testing Datadog RUM Error Tracking"
echo "====================================="

# Check if the application is running
echo "📋 Checking if application is accessible..."
if curl -s -f http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Application is running on localhost:5173"
else
    echo "❌ Application not accessible on localhost:5173"
    echo "   Please start the development server with: npm run dev"
    exit 1
fi

echo ""
echo "🔍 Error Testing Instructions:"
echo "=============================="
echo "1. Open your browser to: http://localhost:5173/error-testing"
echo "2. Log in to your application"
echo "3. Navigate to the Error Testing page"
echo "4. Click the 'Run All Error Tests' button"
echo "5. Check your Datadog RUM dashboard for captured errors"
echo ""
echo "📊 What to look for in Datadog:"
echo "- Error Tracking section should show new errors"
echo "- Look for errors with source: 'browser'"
echo "- Check error types: ReferenceError, TypeError, CustomError, etc."
echo "- Verify stack traces are captured"
echo "- Check if user context and session data is included"
echo ""
echo "🎯 Expected Errors to See:"
echo "- JavaScript ReferenceError (nonExistentVariable)"
echo "- TypeError (null.someProperty)"
echo "- Custom Error (CustomError class)"
echo "- Async Error (Promise rejection)"
echo "- Network Error (HTTP 500 response)"
echo "- Unhandled Promise Rejection"
echo ""
echo "✅ Test Complete!"
echo ""
echo "After running the tests, check your Datadog dashboard at:"
echo "https://app.datadoghq.com/rum/error-tracking"
