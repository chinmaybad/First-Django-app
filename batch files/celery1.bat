@echo off
cmd /k "cd.. & cd /d myenv\Scripts & activate & cd.. & cd.. & celery -A mysite worker --pool=solo"