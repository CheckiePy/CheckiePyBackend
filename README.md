

## Getting started

### 1. Prerequisites

* Python 3.5
* PostgreSQL 9.6
* RabbitMQ 3

### 2. How to use

To deploy the whole system at once you should use [deploy repository](https://github.com/CheckiePy/CheckiePyDeploy). To run only the backend follow this documentation.

#### 2.1. Setup the application

```
git clone https://github.com/CheckiePy/CheckiePyBackend.git
cd CheckiePyBackend
python3 -m venv venv
source venv/bin/activate
pip3 install git+https://github.com/CheckiePy/CheckiePyCore.git@0.16
pip3 install -r requirements.txt
cd acs
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser
```

#### 2.2. Edit hosts

Edit [hosts.py](/acs/hosts.py) file the way you need:

```python
# Hosts for running the application in a local environment

# HOSTNAME = '127.0.0.1'
# POSTGRES_HOST = 'localhost'
# RABBITMQ_HOST = 'localhost'


# Hosts for running the application in a Docker container
# HOSTNAME and WEBHOOK_HOST should be set according to your domain or server IP address

HOSTNAME = 'checkiepy.com'
POSTGRES_HOST = 'postgres'
RABBITMQ_HOST = 'rabbitmq'


# Replace 'https' with 'http' if you don't use a secure connection

WEBHOOK_HOST = 'https://checkiepy.com'
```

#### 2.3. Create a GitHub OAuth App

* Create a new GitHub OAuth App ([documentation](https://developer.github.com/apps/building-oauth-apps/creating-an-oauth-app/)).

* To run the application locally the settings should be like this (the authorization callback URL should be the same as the application `HOSTNAME`):

![OAuth](/docs/oauth.png)

* Provide **Client ID** and **Client Secret** in the next section.

#### 2.4. Provide credentials

Create **credentials.py** file in [acs](/acs) directory:

```python
CLIENT_ID = ''
CLIENT_SECRET = ''
BOT_AUTH = ''
```

How to get `BOT_AUTH` is described in [this](https://github.com/CheckiePy/CheckiePyBackend/tree/master#27-get-bot-auth-credential) section.

#### 2.5. Run Django

```
python3 manage.py runserver
```

#### 2.6. Run Celery

```
celery -A acs worker -l info
```

**Note:**
Django and Celery should be running simultaneously in different command lines (don't forget to run virtual environment in both command lines).

#### 2.7. Get a credential for the bot

* Using bot account login in the application with URL [http://127.0.0.1:8000/login/github/](http://127.0.0.1:8000/login/github/) (adjust the hostname here and further according to your settings).
* Login to admin panel [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with superuser created in section [2.1](https://github.com/CheckiePy/CheckiePyBackend/tree/master#21-setup-the-system).
* Open **User social auths** in **SOCIAL_DJANGO** section.
* Find and open your user.
* Copy **access_token** and paste as `BOT_AUTH` in section [2.4](https://github.com/CheckiePy/CheckiePyBackend/tree/master#24-provide-credentials).

**Note**: You should create a special GitHub user for this purpose.

### 3. API

#### 3.1. Auth

Open in a browser:

```
GET /login/github/
```

After authentication you will be redirected to a url like:
```
/?token=<TOKEN>
```

Now you can take the TOKEN and use it in the rest requests.

### 3.2. Code styles

#### 3.2.1. Create

Create a new code style:

```
POST /api/code_style/create/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Request body:

```json
{
  "name": "Code style name",
  "repository": "Repository url"
}
```

Response body: see the response body for the [read](https://github.com/CheckiePy/CheckiePyBackend/tree/master#322-read) request.

#### 3.2.2. Read

Get a code style info by a id:

```
GET /api/code_style/read/<id>/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Response body (200):

```json
{
    "result":
    {
      "id": 1,
      "name": "Code style name",
      "repository": "Repository url", 
      "calc_status": "S"
    }
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

Calculation status:
* **S** - started
* **F** - failed
* **C** - completed

#### 3.2.3. Delete

Delete a code style by a id:

```
POST /api/code_style/delete/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Request body:

```json
{
  "id": 1
}
```

Response body (200):

```json
{
  "result": 1
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

#### 3.2.4. List

List all completed code styles:

```
GET /api/code_style/list/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Response body (200):

```json
{
    "result":
    [
        {
          "id": 1,
          "name": "Code style name 1",
          "repository": "Repository url 1", 
          "calc_status": "C"
        },
        {
          "id": 2,
          "name": "Code style name 2",
          "repository": "Repository url 2", 
          "calc_status": "C"
        }
    ]
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

The request returns code styles only with **C** calculation status (calc_status).
For calculation status details see [read](https://github.com/CheckiePy/CheckiePyBackend/tree/master#322-read) request.

### 3.3. Repositories

#### 3.3.1. Update

Synchronize the user repository list with GitHub:

```
POST /api/repository/update/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Response body (200):

```json
{
    "result": "Repository update was started"
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

#### 3.3.2. List

List all user repositories:

```
GET /api/repository/list/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Response body (200):

```json
{
    "result":
    [
        {
          "id": 1,
          "name": "Repository name 1",
          "is_connected": false, 
          "code_style_name": "Code style name 2"
        },
        {
          "id": 2,
          "name": "Repository name 2",
          "is_connected": true, 
          "calc_status": "Code style name 1"
        }
    ]
}
```

#### 3.3.3. Last update

Get a date and a status of the last repository synchronization with GitHub:

```
GET /api/repository/last_update/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Response body (200):

```json
{
    "result":
    {
          "datetime": "datetime",
          "status": "S"
    }
}
```

Status:

* **S** - started
* **F** - failed
* **C** - completed

#### 3.3.4. Connect

Connect a code style to a repository by ids:

```
POST /api/repository/connect/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Request body:

```json
{
  "code_style": 1,
  "repository": 2
}
```

Response body (200):

```json
{
    "result":
    {
      "code_style": 1,
      "repository": 2
    }
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

#### 3.3.5. Disconnect

Disconnect a code style from a repository by a id:

```
POST /api/repository/disconnect/
```

Header:
```
Authorization: Token TOKEN
Content-Type: application/json
```

Request body:

```json
{
  "id": 2
}
```

Response body (200):

```json
{
    "result":
    {
      "id": 2
    }
}
```

Response body (4XX):

```json
{
    "detail": "Error description"
}
```

#### 3.3.6. Handle hook

Handle a GitHub webhook for a repository with a id:

```
POST /api/repository/handle_hook/<id>/
```

Request body: the webhook body from GitHub.

Response body (200):

```
true
```

# License

[MIT](/LICENSE)
