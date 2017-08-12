import json
import logging
import config

from celery import shared_task
from github import Github
from django.contrib.auth.models import User
from django.conf import settings
from social_django.models import UserSocialAuth

from . import models
from .reviewer import Requester, Reviewer


logger = logging.getLogger(__name__)


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
    # We need to check repo only if pull request is newly created or received a new commit
    return 'action' in body and (body['action'] == 'opened' or body['action'] == 'synchronize')


@shared_task
def handle_hook(json_body, repository_id):
    try:
        body = json.loads(json_body)
        if not is_need_to_handle_hook(body):
            return
        username = body['repository']['owner']['login']
        pull_request_number = body['number']
        connection = models.GitRepositoryConnection.objects.get(repository=repository_id)
        metrics = json.loads(connection.code_style.metrics)
        base_path = settings.REPOSITORY_DIR
        clone_url = body['repository']['clone_url']
        patch_url = body['pull_request']['patch_url']
        diff_url = body['pull_request']['diff_url']
        requester = Requester(config.BOT_AUTH)
        reviewer = Reviewer(requester, logger)
        reviewer.handle_hook(username, pull_request_number, metrics, base_path, clone_url, patch_url, diff_url)
    except Exception as e:
        logger.exception(e)
