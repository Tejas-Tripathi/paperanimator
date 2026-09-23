import json
import io
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
import os
import subprocess
from .tasks import generate_animation_task
from module_2 import generate_preview_image

@csrf_exempt
def open_file(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        path = data.get('file_path')
        if path and os.path.exists(path):
            os.startfile(path)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def open_location(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        path = data.get('file_path')
        if path and os.path.exists(path):
            os.startfile(os.path.dirname(path))
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
def storage_setting_api(request):
    from .models import StorageSetting
    if request.method == 'GET':
        setting = StorageSetting.get_setting()
        return JsonResponse({'output_path': setting.output_path})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            path = data.get('output_path')
            if not path or not os.path.exists(path):
                return JsonResponse({'success': False, 'error': 'Directory does not exist'})
            if not os.path.isdir(path):
                return JsonResponse({'success': False, 'error': 'Path is not a directory'})
            
            setting = StorageSetting.get_setting()
            setting.output_path = path
            setting.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def browse_storage_path(request):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    try:
        ps_script = (
            'Add-Type -AssemblyName System.Windows.Forms\n'
            '$f = New-Object System.Windows.Forms.FolderBrowserDialog\n'
            '$f.ShowNewFolderButton = $true\n'
            '$dummy = New-Object System.Windows.Forms.Form\n'
            '$dummy.TopLevel = $true\n'
            '$dummy.TopMost = $true\n'
            '$dummy.Opacity = 0\n'
            '$dummy.ShowInTaskbar = $false\n'
            '$dummy.Show()\n'
            '$dummy.Activate()\n'
            "if ($f.ShowDialog($dummy) -eq 'OK') { Write-Output $f.SelectedPath }\n"
            '$dummy.Close()'
        )
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        path = result.stdout.strip()
        return JsonResponse({'success': True, 'path': path})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
        
        from .models import GenerationTask
        GenerationTask.objects.create(
            task_id=task.id,
            file_name=output_filename,
            total_frames=n_images
        )
        
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
        
    try:
        from .models import GenerationTask
        task_record = GenerationTask.objects.get(task_id=task_id)
        response = {
            'task_id': task_record.task_id,
            'file_name': task_record.file_name,
            'status': task_record.status,
            'total_frames': task_record.total_frames,
            'completed_frames': task_record.completed_frames,
            'progress_percentage': task_record.progress_percentage,
            'output_file': task_record.output_file,
            'error': task_record.error
        }
        return JsonResponse(response)
    except Exception as e:
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
