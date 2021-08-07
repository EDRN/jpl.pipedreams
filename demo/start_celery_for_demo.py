from jpl.pipedreams import celeryapp
cd=celeryapp.CeleryDreamer(plugin_list=['plugins'], redis_url='redis://localhost:6379')
cd.start(concurrency=3)

