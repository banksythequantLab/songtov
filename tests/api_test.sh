#!/bin/bash
# Simple test script for MaiVid Studio API endpoints

echo "===== MaiVid Studio API Test ====="
echo "Date: $(date)"
echo

# Test 1: Homepage check
echo "Test 1: Checking if homepage is accessible..."
HOMEPAGE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:420/)
if [ "$HOMEPAGE" == "200" ]; then
  echo "✅ Homepage test PASSED (Status code: $HOMEPAGE)"
else
  echo "❌ Homepage test FAILED (Status code: $HOMEPAGE)"
fi
echo

# Test 2: Check form endpoint with application/x-www-form-urlencoded
echo "Test 2: Testing Convo Pilot download_music API with form data..."
FORM_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "url=https://suno.com/s/H6JQeAvqf4SgiFoF" \
  http://localhost:420/api/convo_pilot/download_music)
if [ "$FORM_TEST" == "200" ]; then
  echo "✅ Form submission test PASSED (Status code: $FORM_TEST)"
else
  echo "❌ Form submission test FAILED (Status code: $FORM_TEST)"
fi
echo

# Test 3: Check JSON endpoint with application/json
echo "Test 3: Testing Convo Pilot download_music API with JSON data..."
JSON_TEST=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://suno.com/s/H6JQeAvqf4SgiFoF"}' \
  http://localhost:420/api/convo_pilot/download_music)
if [ "$JSON_TEST" == "200" ]; then
  echo "✅ JSON submission test PASSED (Status code: $JSON_TEST)"
else
  echo "❌ JSON submission test FAILED (Status code: $JSON_TEST)"
fi
echo

echo "===== Test Summary ====="
echo "Homepage: $HOMEPAGE"
echo "Form submission: $FORM_TEST"
echo "JSON submission: $JSON_TEST"
echo
echo "Tests completed at $(date)"
