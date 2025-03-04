# Commands

Here are some commands on how to run certain things

## Run the cli version

```bash
python main.py --{webcam/image/video} # also need to provide the path to image/video if using image/video as arguement

``` 
## Run the flask server

```bash
python app.py
```

## Run the tests

```bash
pytest tests/test_api.py -v
pytest tests/test_streaming.py -v
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


