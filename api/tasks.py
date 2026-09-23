from celery import shared_task
from module_2 import generate_animation_video
from .models import GenerationTask

@shared_task(bind=True)
def generate_animation_task(self, target_text, aspect_ratio_key, n_images, output_filename=None, config=None):
    try:
        from .models import GenerationTask, StorageSetting
        task_record = GenerationTask.objects.get(task_id=self.request.id)
        task_record.status = 'RUNNING'
        task_record.save()
        
        setting = StorageSetting.get_setting()
        output_dir = setting.output_path
        
        def update_progress(completed, total):
            task_record.completed_frames = completed
            task_record.progress_percentage = (completed / total) * 100
            task_record.save()

        output_path = generate_animation_video(
            target_text, 
            aspect_ratio_key, 
            n_images, 
            output_filename, 
            config=config,
            progress_callback=update_progress,
            output_dir=output_dir
        )
        
        task_record.status = 'SUCCESS'
        task_record.completed_frames = n_images
        task_record.progress_percentage = 100
        task_record.output_file = output_path
        task_record.save()
        
        return {
            'output_file': output_path,
            'file_name': output_filename
        }
    except Exception as e:
        try:
            task_record = GenerationTask.objects.get(task_id=self.request.id)
            task_record.status = 'FAILURE'
            task_record.error = str(e)
            task_record.save()
        except Exception:
            pass
        raise e
