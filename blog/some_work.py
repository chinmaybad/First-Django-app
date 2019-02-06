import time
import logging
logger = logging.getLogger(__name__)

class Work(object):
    def __init__(self, task):
        self.task=task
    def run(self):
        logger.info('Task started : id = '+str(self.task))
        for i in range(0,100):
            print('Current : '+ str(i))
            self.task.update_state(state='PROGRESS',meta={'current':i})
            time.sleep(0.2)
        logger.info('Task Completed')