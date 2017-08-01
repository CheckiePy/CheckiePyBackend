

## Getting started

### 1. Prerequisites

* Python 3.5

### 2. Setup and run

```
git clone https://github.com/acsproj/acsbackend.git
cd acsbackend
python3 -m venv venv
source venv/bin/activate
pip3 install git+https://github.com/acsproj/acscore.git@0.10
pip3 install -r requirements.txt
cd acs
python3 manage.py runserver
```

**Note:**
For async tasks RabbitMQ is required. Start a celery worker with this command:

```
celery -A acs worker -l info
```
### 3. API

* TODO

# License

The MIT License (MIT) Copyright (c) 2017 Artem Ustimov

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.