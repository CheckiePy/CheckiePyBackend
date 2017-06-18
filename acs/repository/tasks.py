import os
import json
import shutil
import requests

from celery import shared_task
from github import Github
from django.contrib.auth.models import User
from django.conf import settings
from dulwich import porcelain
from social_django.models import UserSocialAuth
from subprocess import Popen, PIPE, STDOUT
from acscore.counter import Counter
from acscore.analyzer import Analyzer
from unidiff import PatchSet

from . import models

ACTION = 'action'
OPENED = 'opened'
SYNCHRONIZE = 'synchronize'
REPOSITORY = 'repository'
CLONE_URL = 'clone_url'
PULL_REQUEST = 'pull_request'
PATCH_URL = 'patch_url'
DIFF_URL = 'diff_url'
PATCH_FILENAME = 'p.patch' # This name is used in applypatch.sh
DIFF_FILENAME = 'd.diff'
BOT_NAME = 'UPlatformTeam'
NAME = 'name'
OWNER = 'owner'
LOGIN = 'login'
NUMBER = 'number'


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


def is_need_to_handle_hook(body):
    # We need to check repo only if pull request is newly created or received a new commit.
    if ACTION in body and (body[ACTION] == OPENED or body[ACTION] == SYNCHRONIZE):
        return True
    return False


def clone_repo(body):
    clone_url = body[REPOSITORY][CLONE_URL]

    # Todo: hashed name for repo to get unique path
    name = os.path.basename(os.path.normpath(clone_url))
    path = os.path.join(settings.REPOSITORY_DIR, name)
    if os.path.exists(path):
        shutil.rmtree(path)
    porcelain.clone(clone_url, path)
    return path


def save_patch(body, repo_path):
    patch_url = body[PULL_REQUEST][PATCH_URL]
    patch = requests.get(patch_url)
    with open(os.path.join(repo_path, PATCH_FILENAME), 'w') as p:
        p.write(patch.content.decode())


def apply_patch(repo_path):
    # Todo: pass patch filename as argument
    message = run_command(["{0}/bash/applypatch.sh".format(settings.BASE_DIR), repo_path])
    # print(message)


def save_diff(body, repo_path):
    diff_url = body[PULL_REQUEST][DIFF_URL]
    diff = requests.get(diff_url)
    diff_path = os.path.join(repo_path, DIFF_FILENAME)
    with open(diff_path, 'w') as d:
        d.write(diff.content.decode())


def access_to_repo_as_bot(body, bot_name):
    repo_name = body[REPOSITORY][NAME]
    owner = body[REPOSITORY][OWNER][LOGIN]
    user, access_token = get_credentials(bot_name)
    github = Github(bot_name, access_token)
    github_user = github.get_user(owner)
    github_repo = github_user.get_repo(repo_name)
    return github_repo


def get_pull_request_and_latest_commit(body, github_repo):
    pull_request = github_repo.get_pull(body[NUMBER])
    # Todo: check if comment to latest commit is ok when style violation in previous commit
    commit = pull_request.get_commits().reversed[0]
    return pull_request, commit


def review_repo(repository_id, repo_path, pull_request, commit):
    # Todo: refactor
    connection = models.GitRepositoryConnection.objects.get(repository=repository_id)
    repo_metrics = json.loads(connection.code_style.metrics)
    analyzer = Analyzer(repo_metrics)
    counter = Counter()
    with open(os.path.join(repo_path, DIFF_FILENAME), 'r') as d:
        patch_set = PatchSet(d)

    mentioned = {}
    for patch in patch_set:
        file_metrics = counter.metrics_for_file(os.path.join(repo_path, patch.path), verbose=True)
        #print('METRICS', file_metrics)
        inspections = analyzer.inspect(file_metrics)
        for hunk in patch:
            #print('INSPECTIONS', inspections)
            for metric_name, inspection_value in inspections.items():
                for inspection, value in inspection_value.items():
                    #print('VALUE', value)
                    if inspection in mentioned:
                        continue
                    elif 'lines' not in value:
                        mentioned[inspection] = True
                        pull_request.create_issue_comment('{0}:\n{1}'.format(patch.path, value['message']))
                    else:
                        for line in value['lines']:
                            if hunk.target_start <= line <= hunk.target_start + hunk.target_length:
                                print('CREATE COMMENT', value['message'])
                                pull_request.create_comment(value['message'], commit, patch.path, line - hunk.target_start + 1)


@shared_task
def handle_hook(json_body, repository_id):
    body = json.loads(json_body)

    if not is_need_to_handle_hook(body):
        return

    repo_path = clone_repo(body)
    save_patch(body, repo_path)
    apply_patch(repo_path)
    save_diff(body, repo_path)

    github_repo = access_to_repo_as_bot(body, BOT_NAME)
    pull_request, commit = get_pull_request_and_latest_commit(body, github_repo)

    # Todo: record mentioned violations
    review_repo(repository_id, repo_path, pull_request, commit)

    shutil.rmtree(repo_path)

