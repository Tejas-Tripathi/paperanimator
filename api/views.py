import json
import io
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from .tasks import generate_animation_task
from module_2 import generate_preview_image

def index(request):
    return render(request, 'api/index.html')

@csrf_exempt
def generate_preview(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        target_text = data.get('target_text', 'Sample Target')
        if not target_text: target_text = 'Sample Target'
        
        aspect_ratio_key = data.get('aspect_ratio', '1')
        settings = data.get('settings', None)
        
        img = generate_preview_image(target_text, str(aspect_ratio_key), config=settings)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return HttpResponse(buffer.getvalue(), content_type='image/png')
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def generate_animation(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method is allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        
        target_text = data.get('target_text')
        aspect_ratio_key = data.get('aspect_ratio', '1') # default 9:16
        n_images = data.get('n_images', 12)
        output_filename = data.get('file_name', None)
        settings = data.get('settings', None)
        
        if not target_text:
            return JsonResponse({'success': False, 'error': 'target_text is required'}, status=400)
            
        try:
            n_images = int(n_images)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'n_images must be an integer'}, status=400)
            
        task = generate_animation_task.delay(target_text, str(aspect_ratio_key), n_images, output_filename, config=settings)
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'status': 'PENDING'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def get_task_status(request, task_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)
        
    task_result = AsyncResult(task_id)
    response = {
        'task_id': task_id,
        'status': task_result.status
    }
    
    if task_result.status == 'SUCCESS':
        response['result'] = task_result.result
    elif task_result.status == 'FAILURE':
        response['error'] = str(task_result.info)
        
    return JsonResponse(response)
