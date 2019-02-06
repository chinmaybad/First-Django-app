from __future__ import absolute_import, unicode_literals
from celery import task, shared_task
import time
from .some_work import Work
# this decorator is all that's needed to tell celery this is a worker task
@task(bind=True)
def do_work(self):  
    time.sleep(2)
    w = Work(self)
    w.run()
    # for i in range(100):
    #     print('working on : ' +i)
    #     time.sleep(400)
    #     self.update_state(
    #         state=PROGRESS_STATE,
    #         meta={
    #             'current': i,
    #             'total': 100,
    #         }
    #     )        
        # tell the progress observer how many out of the total items we have processed
        # progress_observer.set_progress(i, total_work_to_do)

"""
#Setting the state
task.update_state(
    state=PROGRESS_STATE,
    meta={
        'current': current,
        'total': total,
    }
)


#Reading the state
from celery.result import AsyncResult
result = AsyncResult(task_id)
print(result.state)  # will be set to PROGRESS_STATE
print(result.info)  # metadata will be here


Solution to error :- JSON dumps
Another working solution is to use eventlet (`pip install eventlet` ->
`celery -A your_app_name worker --pool=eventlet`).
This way it is possible to have parallel-running tasks on Windows.

"""