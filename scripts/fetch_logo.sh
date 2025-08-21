#!/bin/bash

# Usage: ./fetch_logo.sh <FLAVOR_ID> <API_KEY> [OUTPUT_PATH] [--quiet]
FLAVOR_ID=$1
PROJECT_API_KEY=$2
OUTPUT_PATH=${3:-"./logo"}
QUIET_MODE=false

# Check for --quiet flag
if [[ "$*" == *"--quiet"* ]]; then
    QUIET_MODE=true
fi

# Validate required parameters
if [ -z "$PROJECT_API_KEY" ] || [ -z "$FLAVOR_ID" ]; then
    echo "Usage: $0 <FLAVOR_ID> <API_KEY> [OUTPUT_PATH] [--quiet]"
    echo "Example: $0 6e858ca5-6159-4171-987c-f2929b2a329f your-api-key ./logos/client-logo"
    echo "  --quiet: Only output the final file path on success"
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_PATH")
mkdir -p "$OUTPUT_DIR"

# Download the logo file
if [ "$QUIET_MODE" = false ]; then
    echo "Downloading logo for flavor ID: $FLAVOR_ID with API key: $PROJECT_API_KEY"
fi
# exit 1
# First, get the file with headers to determine the content type and extension
TEMP_FILE=$(mktemp)
curl -L -X GET \
    -H "Authorization: Bearer $PROJECT_API_KEY" \
    -H "Accept: image/*" \
    --output "$TEMP_FILE" \
    --show-error \
    --fail \
    --dump-header /tmp/curl_headers_$$ \
    "https://ilesfsxvmvavrlmojmba.supabase.co/functions/v1/project-flavor-logo?id=$FLAVOR_ID"

# Check if download was successful
if [ $? -ne 0 ] || [ ! -f "$TEMP_FILE" ]; then
    if [ "$QUIET_MODE" = false ]; then
        echo "Failed to download logo for flavor ID: $FLAVOR_ID"
    fi
    rm -f "$TEMP_FILE" /tmp/curl_headers_$$
    exit 1
fi

# Determine file extension from Content-Type header
CONTENT_TYPE=$(grep -i "content-type:" /tmp/curl_headers_$$ | cut -d: -f2 | tr -d ' \r\n' || echo "")
EXTENSION=""

case "$CONTENT_TYPE" in
    *"image/svg+xml"*) EXTENSION=".svg" ;;
    *"image/png"*) EXTENSION=".png" ;;
    *"image/jpeg"*) EXTENSION=".jpg" ;;
    *"image/jpg"*) EXTENSION=".jpg" ;;
    *"image/gif"*) EXTENSION=".gif" ;;
    *"image/webp"*) EXTENSION=".webp" ;;
    *) 
        # Try to detect from file content if Content-Type is not available
        if file "$TEMP_FILE" | grep -q "SVG"; then
            EXTENSION=".svg"
        elif file "$TEMP_FILE" | grep -q "PNG"; then
            EXTENSION=".png"
        elif file "$TEMP_FILE" | grep -q "JPEG"; then
            EXTENSION=".jpg"
        else
            EXTENSION=".png"  # Default fallback
        fi
        ;;
esac

# Create final output path with proper extension
FINAL_OUTPUT_PATH="${OUTPUT_PATH}${EXTENSION}"
OUTPUT_DIR=$(dirname "$FINAL_OUTPUT_PATH")
mkdir -p "$OUTPUT_DIR"

# Move the temporary file to final location
mv "$TEMP_FILE" "$FINAL_OUTPUT_PATH"

# Clean up header file
rm -f /tmp/curl_headers_$$

# Check if final file exists and report success
if [ -f "$FINAL_OUTPUT_PATH" ]; then
    if [ "$QUIET_MODE" = true ]; then
        # In quiet mode, only output the file path
        echo "$FINAL_OUTPUT_PATH"
    else
        echo "Logo downloaded successfully: $FINAL_OUTPUT_PATH"
        echo "File size: $(du -h "$FINAL_OUTPUT_PATH" | cut -f1)"
        echo "Content type: $CONTENT_TYPE"
    fi
    exit 0
else
    if [ "$QUIET_MODE" = false ]; then
        echo "Failed to download logo for flavor ID: $FLAVOR_ID"
    fi
    exit 1
fi