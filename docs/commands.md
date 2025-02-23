# Some commands

## Run the server

```bash
python src/web/app.py
```

## Run the tests

```bash
pytest tests/test_api.py -v
```

## Run the tests in a specific browser

```bash
pytest tests/test_api.py -v --browser=chrome
```

## Run Memurai server

```bash
memurai.exe --service-start
```
or
```bash
net start memurai
```

## Stop Memurai Server

```bash
memurai.exe --service-stop
```
or
```bash
net stop memurai
```

## Run Celery worker on windows

```bash
celery -A src.web.tasks worker --pool=solo --loglevel=info
```


