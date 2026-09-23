import requests

url = 'http://127.0.0.1:8000/api/generate/'
data = {
    'target_text': 'Paper',
    'aspect_ratio': '3', # 1:1
    'n_images': 2
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
