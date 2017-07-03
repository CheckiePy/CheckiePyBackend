import os
import json
import shutil
import requests
import logging
import io

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
BOT_NAME = 'acsproj-bot'
NAME = 'name'
OWNER = 'owner'
LOGIN = 'login'
NUMBER = 'number'

logger = logging.getLogger(__name__)


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
        github_repository.create_hook('web', {'url': settings.WEBHOOK_URL + str(repository_id) + '/', 'content_type': 'json'}, ['pull_request'],
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

    logger.info('Started cloning repo from {0} to {1}'.format(clone_url, path))

    if os.path.exists(path):

        logger.info('Repo at {0} already exists. Deleting it'.format(path))

        shutil.rmtree(path)

    bytes_io = io.BytesIO()
    porcelain.clone(clone_url, path, errstream=bytes_io)

    logger.info(bytes_io.getvalue().decode())

    logger.info('Repo successfully cloned')

    return path


def save_patch(body, repo_path):
    patch_url = body[PULL_REQUEST][PATCH_URL]
    path = os.path.join(repo_path, PATCH_FILENAME)

    logger.info('Starting downloading of path file from {0} to {1}'.format(patch_url, path))

    patch = requests.get(patch_url)
    with open(path, 'w') as p:
        p.write(patch.content.decode())

        logger.info('Patch file successfully downloaded')


def apply_patch(repo_path):
    logger.info('Applying the patch')

    # Todo: pass patch filename as argument
    message = run_command(["{0}/bash/applypatch.sh".format(settings.BASE_DIR), repo_path])

    logger.info(message)


def save_diff(body, repo_path):
    diff_url = body[PULL_REQUEST][DIFF_URL]
    diff_path = os.path.join(repo_path, DIFF_FILENAME)

    logger.info('Starting downloading diff file from {0} to {1}'.format(diff_url, diff_path))

    diff = requests.get(diff_url)
    with open(diff_path, 'w') as d:
        d.write(diff.content.decode())

        logger.info('Diff file successfully downloaded')


def access_to_repo_as_bot(body, bot_name):
    repo_name = body[REPOSITORY][NAME]
    owner = body[REPOSITORY][OWNER][LOGIN]

    logger.info('Trying to get access to {0} repo of {1} with bot {2}'.format(repo_name, owner, bot_name))

    user, access_token = get_credentials(bot_name)
    github = Github(bot_name, access_token)
    github_user = github.get_user(owner)
    github_repo = github_user.get_repo(repo_name)

    logger.info('Access successfully gained')

    return github_repo


def get_pull_request_and_latest_commit(body, github_repo):
    pull_request = github_repo.get_pull(body[NUMBER])

    logger.info('Got pull request with titile {0} and number {1}'.format(pull_request.title, pull_request.number))

    # Todo: check if comment to latest commit is ok when style violation in previous commit
    commit = pull_request.get_commits().reversed[0]

    logger.info('Got commit with sha {0}'.format(commit.sha))

    return pull_request, commit


def review_repo(repository_id, repo_path, pull_request, commit):
    logger.info('Starting review')

    # Todo: refactor
    connection = models.GitRepositoryConnection.objects.get(repository=repository_id)
    repo_metrics = json.loads(connection.code_style.metrics)
    analyzer = Analyzer(repo_metrics)
    counter = Counter()
    with open(os.path.join(repo_path, DIFF_FILENAME), 'r') as d:
        patch_set = PatchSet(d)

    comments_sent = 0

    mentioned = {}
    for patch in patch_set:
        file_metrics = counter.metrics_for_file(os.path.join(repo_path, patch.path), verbose=True)

        logger.info('Metrics for file {0} {1}'.format(patch.path, file_metrics))

        inspections = analyzer.inspect(file_metrics)
        first_line_in_diff = patch[0][0].diff_line_no
        for hunk in patch:

            logger.info('Inspections for file {0} {1}'.format(patch.path, inspections))

            for metric_name, inspection_value in inspections.items():
                for inspection, value in inspection_value.items():

                    logger.info('Inspection {0} has value {1}'.format(inspection, value))

                    if inspection in mentioned:
                        continue
                    elif 'lines' not in value:
                        mentioned[inspection] = True

                        logger.info('Issue comment {0} to file {1}'.format(value['message'], patch.path))

                        pull_request.create_issue_comment('{0}:\n{1}'.format(patch.path, value['message']))
                        comments_sent += 1
                    else:
                        for line in value['lines']:
                            if hunk.target_start <= line <= hunk.target_start + hunk.target_length:

                                line_object = hunk[line - hunk.target_start + 3]
                                target_line = line_object.diff_line_no - first_line_in_diff

                                logger.info('Calculated line with #{0} and value {1}'.format(line_object.diff_line_no, line_object.value))
                                logger.info('Comment file {0} on line {1} with message {2}'.format(patch.path, line, value['message']))
                                logger.info('Hunk from {0} to {1}'.format(hunk.target_start, hunk.target_start + hunk.target_length))

                                pull_request.create_comment(value['message'], commit, patch.path, target_line)
                                comments_sent += 1
    if comments_sent == 0:
        pull_request.create_issue_comment('Repository was reviewed. Everything is alright')

        logger.info('Everything is alrigth')


@shared_task
def handle_hook(json_body, repository_id):

    print(logger)

    try:
        body = json.loads(json_body)

        if not is_need_to_handle_hook(body):
            return

        logger.info('Started review for repo id {0}'.format(repository_id))

        repo_path = clone_repo(body)
        save_patch(body, repo_path)
        apply_patch(repo_path)
        save_diff(body, repo_path)

        github_repo = access_to_repo_as_bot(body, BOT_NAME)
        pull_request, commit = get_pull_request_and_latest_commit(body, github_repo)

        # Todo: record mentioned violations
        review_repo(repository_id, repo_path, pull_request, commit)

        shutil.rmtree(repo_path)

        logger.info('Repo {0} review successfully completed'.format(repository_id))
    except Exception as e:
        logger.exception(e)


