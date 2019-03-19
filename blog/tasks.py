from __future__ import absolute_import, unicode_literals
from celery import task, shared_task
from celery.signals import task_revoked, task_success, task_failure
import time
from .some_work import Work

# this decorator is all that's needed to tell celery this is a worker task
@task(bind=True)
def do_work(self):  
    # time.sleep(2)
    w = Work(self)
    w.run()
    

@task_revoked.connect
def on_task_revoked(*args, **kwargs):
    # print(str(kwargs))
    print('### some task_revoked')

"""

#Reading the stated
from celery.result import AsyncResult
result = AsyncResult(task_id)
print(result.state)  # will be set to PROGRESS_STATE
print(result.info)  # metadata will be here


Solution to error :- JSON dumps
Another working solution is to use eventlet (`pip install eventlet` ->
`celery -A your_app_name worker --pool=eventlet`).
This way it is possible to have parallel-running tasks on Windows.

"""