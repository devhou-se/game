#!/usr/bin/env python3
import os
import json
import base64
from tempfile import NamedTemporaryFile
from google.cloud import storage

# Get post ID
post_id = os.environ.get("POST_ID")

# Setup GCS client
gcs_credentials_json = os.environ.get("GCS_CREDENTIALS")
gcs_bucket_name = os.environ.get("GCS_BUCKET")

def upload_to_gcs():
    """Upload audio files to Google Cloud Storage"""
    # Create a temporary file for credentials
    with NamedTemporaryFile(mode='w', delete=False) as temp:
        temp.write(gcs_credentials_json)
        temp_name = temp.name
    
    try:
        # Setup GCS client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_name
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        
        # Load audio references
        with open(f"generated/audio-refs-{post_id}.json", 'r') as f:
            audio_refs = json.load(f)
        
        # Upload English audio files
        for category in ["greetings", "reactions"]:
            if category == "greetings":
                for item in audio_refs["en"][category]:
                    local_path = f"generated/{item['file']}"
                    remote_path = item['file']
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_path)
            elif category == "reactions":
                for emotion, reactions in audio_refs["en"][category].items():
                    for item in reactions:
                        local_path = f"generated/{item['file']}"
                        remote_path = item['file']
                        blob = bucket.blob(remote_path)
                        blob.upload_from_filename(local_path)
        
        # Upload English topic audio files
        for topic, items in audio_refs["en"]["topics"].items():
            for item in items:
                local_path = f"generated/{item['file']}"
                remote_path = item['file']
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
        
        # Upload Japanese audio files
        for category in ["greetings", "reactions"]:
            if category == "greetings":
                for item in audio_refs["ja"][category]:
                    local_path = f"generated/{item['file']}"
                    remote_path = item['file']
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_path)
            elif category == "reactions":
                for emotion, reactions in audio_refs["ja"][category].items():
                    for item in reactions:
                        local_path = f"generated/{item['file']}"
                        remote_path = item['file']
                        blob = bucket.blob(remote_path)
                        blob.upload_from_filename(local_path)
        
        # Upload Japanese topic audio files
        for topic, items in audio_refs["ja"]["topics"].items():
            for item in items:
                local_path = f"generated/{item['file']}"
                remote_path = item['file']
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
        
        print(f"Uploaded audio files to GCS bucket '{gcs_bucket_name}'")
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_name):
            os.unlink(temp_name)

if __name__ == "__main__":
    upload_to_gcs()