import requests
import time

base_url = 'http://127.0.0.1:8000/api/generate/'
data = {
    'target_text': 'Async Celery',
    'aspect_ratio': '1', # 1:1
    'n_images': 2
}

try:
    print("Sending POST request...")
    response = requests.post(base_url, json=data)
    print(f"Status Code: {response.status_code}")
    res_json = response.json()
    print(f"Response: {res_json}")
    
    if res_json.get('success'):
        task_id = res_json.get('task_id')
        print(f"\nPolling status for task_id: {task_id}")
        
        while True:
            time.sleep(2)
            status_response = requests.get(f"{base_url}status/{task_id}/")
            status_json = status_response.json()
            print(f"Status: {status_json}")
            
            if status_json.get('status') in ['SUCCESS', 'FAILURE']:
                break
                
except Exception as e:
    print(f"Error: {e}")
