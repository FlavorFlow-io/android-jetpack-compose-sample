#!/bin/bash
PROJECT_API_KEY=$1
curl -X GET   -H "Authorization: Bearer $PROJECT_API_KEY"   -H "Accept: application/json"   https://ilesfsxvmvavrlmojmba.supabase.co/functions/v1/project-flavors