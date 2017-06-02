import os
import json
import shutil
import requests

from celery import shared_task
from github import Github
from django.contrib.auth.models import User
from django.conf import settings
from dulwich import porcelain
from dulwich.repo import Repo
from social_django.models import UserSocialAuth
from subprocess import Popen, PIPE, STDOUT
from acscore.counter import Counter

from . import models


def run_command(command):
    p = Popen(command, stdout=PIPE, stderr=STDOUT)
    result = ''
    for line in p.stdout.readlines():
        result += line.decode() + '\n'
    return result


def get_credentials(username):
    user = User.objects.get(username=username)
    user_social_auth = UserSocialAuth.objects.get(user=user)
    access_token = user_social_auth.extra_data['access_token']
    return user, access_token


@shared_task
def load_user_repositories(username, update_id):
    update = models.GitRepositoryUpdate.objects.get(id=update_id)
    try:
        user, access_token = get_credentials(username)
        github = Github(username, access_token)
        repositories = github.get_user().get_repos()
        for repository in repositories:
            models.GitRepository.objects.get_or_create(user=user, name=repository.name)
        update.status = 'C'
    except Exception as e:
        print(e)
        update.status = 'F'
    finally:
        update.save()


@shared_task
def set_hook(username, repository_id):
    try:
        repository = models.GitRepository.objects.get(id=repository_id)
        user, access_token = get_credentials(username)
        github = Github(username, access_token)
        github_user = github.get_user(username)
        github_repository = github_user.get_repo(repository.name)
        github_repository.create_hook('web', {'url': settings.WEBHOOK_URL, 'content_type': 'json'}, ['pull_request'],
                                      True)
        repository.is_connected = True
        repository.save()
    except Exception as e:
        print(e)


@shared_task
def handle_hook(body):
    body = json.loads(body)

    # Handle only "opened" action
    if 'action' not in body or body['action'] != 'opened':
        return

    repo_name = body['repository']['name']
    owner = body['repository']['owner']['login']

    diff_url = body['pull_request']['diff_url']
    patch_url = body['pull_request']['patch_url']
    clone_url = body['repository']['clone_url']

    name = os.path.basename(os.path.normpath(clone_url))
    path = os.path.join(settings.REPOSITORY_DIR, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    porcelain.clone(clone_url, path)

    diff = requests.get(diff_url)
    patch = requests.get(patch_url)

    d = open(os.path.join(path, 'd.diff'), 'w')
    d.write(diff.content.decode())
    d.close()

    p = open(os.path.join(path, 'p.patch'), 'w')
    p.write(patch.content.decode())
    p.close()

    repo = Repo(path)
    old_commit = repo.head().decode()
    print(old_commit)

    message = run_command(["{0}/bash/applypatch.sh".format(settings.BASE_DIR), path])
    print(message)

    new_commit = repo.head().decode()
    print(new_commit)

    message = run_command(["{0}/bash/changedfiles.sh".format(settings.BASE_DIR), path, old_commit, new_commit])
    print(message)

    changed_files = list(filter(lambda item: item != '', message.split('\n')))

    print(changed_files)

    counter = Counter()
    for file in changed_files:
        metrics = counter.metrics_for_file(os.path.join(path, file))
        print(metrics)

    username = 'UPlatformTeam'
    user, access_token = get_credentials(username)
    github = Github(username, access_token)
    github_user = github.get_user(owner)
    github_repo = github_user.get_repo(repo_name)

    pull = github_repo.get_pulls()[0]
    pull.create_issue_comment('Metrics counted')

    shutil.rmtree(path)

