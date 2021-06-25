from celery import Celery

BROKER_URL = 'redis://localhost:6379/0'
BACKEND_URL = 'redis://localhost:6379/1'
app = Celery('proj',
             broker=BROKER_URL,
             backend=BACKEND_URL,
             include=['jpl.pipedreams.celery_task_registry'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
        serializer='pickle',
        result_serializer='pickle',
        task_serializer='pickle',
        accept_content=['pickle', 'json'],
        result_accept_content=['pickle', 'json']
)

if __name__ == '__main__':
    app.start()


# run a single worker
# >> celery -A jpl.pipedreams.celeryapp:app worker -l INFO --concurrency=2 -n worker1
# kill stray celery processes:
# >> sudo pkill -f celery

"""
ref: 
https://stackoverflow.com/questions/19926750/django-importerror-cannot-import-name-celery-possible-circular-import
https://stackoverflow.com/questions/31898311/celery-difference-between-concurrency-workers-and-autoscaling
"""