import os
import json
import shutil

from acscore.counter import Counter
from celery import shared_task
from django.conf import settings
from dulwich import porcelain

from . import models


@shared_task
def calc_metrics(code_style_id):
    code_style = models.CodeStyle.objects.get(id=code_style_id)
    try:
        path = os.path.join(settings.REPOSITORY_DIR, str(code_style.id))
        porcelain.clone(code_style.repository, path)
        counter = Counter()
        code_style.metrics = json.dumps(counter.metrics_for_dir(path))
        code_style.calc_status = 'C'
        shutil.rmtree(path)
    except Exception as e:
        print(e)
        code_style.calc_status = 'F'
    finally:
        code_style.save()