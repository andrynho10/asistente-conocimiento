#!/usr/bin/env python3

import requests
import tempfile
import os

# Test endpoint directly
url = "http://localhost:8000/api/knowledge/upload"

# Create a fake docx file
with tempfile.NamedTemporaryFile(mode='wb', suffix='.docx', delete=False) as tmp:
    tmp.write(b"fake docx content")
    tmp_path = tmp.name

try:
    with open(tmp_path, 'rb') as test_file:
        files = {"file": ("test.docx", test_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        data = {
            "title": "Documento Word",
            "category": "test_category"
        }
        headers = {"Authorization": "Bearer fake_token"}

        response = requests.post(url, files=files, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

finally:
    os.unlink(tmp_path)