from celery import shared_task
from github import Github
from django.contrib.auth.models import User
from django.conf import settings
from social_django.models import UserSocialAuth

from . import models


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