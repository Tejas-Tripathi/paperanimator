from django.db import models

class GenerationTask(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='PENDING')
    total_frames = models.IntegerField(default=0)
    completed_frames = models.IntegerField(default=0)
    progress_percentage = models.FloatField(default=0)
    output_file = models.CharField(max_length=1000, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_id} - {self.status}"

class StorageSetting(models.Model):
    output_path = models.CharField(max_length=1000)
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super(StorageSetting, self).save(*args, **kwargs)
        
    @classmethod
    def get_setting(cls):
        from module_1 import OUTPUT_DIR
        obj, created = cls.objects.get_or_create(pk=1, defaults={'output_path': str(OUTPUT_DIR)})
        return obj
