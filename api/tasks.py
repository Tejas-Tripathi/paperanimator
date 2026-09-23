from celery import shared_task
from module_2 import generate_animation_video

@shared_task(bind=True)
def generate_animation_task(self, target_text, aspect_ratio_key, n_images, output_filename=None, config=None):
    try:
        self.update_state(state='PROGRESS')
        output_path = generate_animation_video(target_text, aspect_ratio_key, n_images, output_filename, config=config)
        return {
            'output_file': output_path,
            'file_name': output_filename
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc': str(e)})
        raise e
