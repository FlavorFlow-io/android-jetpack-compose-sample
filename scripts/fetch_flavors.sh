#!/bin/bash

# Usage: ./fetch_flavors.sh <API_KEY> [--quiet]
PROJECT_API_KEY=$1
QUIET_MODE=false

# Check for --quiet flag
if [[ "$*" == *"--quiet"* ]]; then
    QUIET_MODE=true
fi

# Validate required parameters
if [ -z "$PROJECT_API_KEY" ]; then
    echo "Usage: $0 <PROJECT_API_KEY> [--quiet]"
    echo "Example: $0 1234567890"
    echo "  --quiet: Only output the JSON response"
    exit 1
fi

# Fetch flavors from API
if [ "$QUIET_MODE" = false ]; then
    echo "Fetching flavors with API key: $PROJECT_API_KEY"
fi

# Make the API call and capture response
RESPONSE=$(curl -L -X GET \
    -H "Authorization: Bearer $PROJECT_API_KEY" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    --silent \
    --show-error \
    "https://ilesfsxvmvavrlmojmba.supabase.co/functions/v1/project-flavors")

# Check if curl command was successful
CURL_EXIT_CODE=$?
if [ $CURL_EXIT_CODE -ne 0 ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo "Failed to fetch flavors. Curl exit code: $CURL_EXIT_CODE"
    fi
    exit 1
fi

# Check if response is empty
if [ -z "$RESPONSE" ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo "Empty response from API"
    fi
    exit 1
fi

# Validate JSON format (optional check)
if command -v jq &> /dev/null; then
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        if [ "$QUIET_MODE" = false ]; then
            echo "Warning: Response is not valid JSON format"
        fi
    fi
fi

# Output results
if [ "$QUIET_MODE" = true ]; then
    # In quiet mode, only output the JSON response
    echo "$RESPONSE"
else
    echo "Flavors fetched successfully and saved to: $OUTPUT_PATH"
    echo "Response:"
    echo "$RESPONSE"
fi

exit 0