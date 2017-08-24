import os
import io
import shutil
import requests

from github import Github
from dulwich import porcelain
from acscore.counter import Counter
from acscore.analyzer import Analyzer
from unidiff import PatchSet
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from subprocess import Popen, PIPE, STDOUT
from django.conf import settings


SETTINGS = {
    'name': 'CheckiePy',
    'url': 'http://checkiepy.com',
    'attempt': 3,
    'multiplier': 2,
    'max': 10,
    'apply': '{0}/bash/apply_patch.sh'.format(settings.BASE_DIR),
}


class Logger:
    def info(self, text):
        print(text)


class Requester:
    def __init__(self, access_token, bot_access_token=None):
        self.github = Github(access_token)
        if bot_access_token:
            self.bot = Github(bot_access_token)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def get_repositories(self, username):
        return self.github.get_user(username).get_repos()

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_pull_request_hook(self, username, repository_name, callback_url):
        self.github.get_user(username).get_repo(repository_name)\
            .create_hook('web', {'url': callback_url, 'content_type': 'json'}, ['pull_request'], True)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def delete_pull_request_hook(self, username, repository_name, callback_url):
        hooks = self.github.get_user(username).get_repo(repository_name).get_hooks()
        for hook in hooks:
            if hook.config['url'] == callback_url:
                hook.delete()

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def clone_repository(self, clone_url, save_path, bytes_io):
        if os.path.exists(save_path):
            shutil.rmtree(save_path)
        porcelain.clone(clone_url, save_path, errstream=bytes_io)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def get_file(self, file_url):
        return requests.get(file_url)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def get_pull_request(self, username, repository_name, pull_request_number):
        return self.github.get_user(username).get_repo(repository_name).get_pull(pull_request_number)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def get_latest_commit_from_pull_request(self, pull_request):
        return pull_request.get_commits().reversed[0]

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_status(self, commit, state, target_url, description, context):
        commit.create_status(state, target_url, description, context)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_issue_comment(self, pull_request, text):
        pull_request.create_issue_comment(text)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_comment(self, pull_request, text, commit, file, line):
        pull_request.create_comment(text, commit, file, line)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_issue_comment_bot(self, username, repository_name, pull_request_number, text):
        self.bot.get_user(username).get_repo(repository_name).get_pull(pull_request_number).create_issue_comment(text)

    @retry(stop=stop_after_attempt(SETTINGS['attempt']),
           wait=wait_exponential(multiplier=SETTINGS['multiplier'], max=SETTINGS['max']))
    def create_comment_bot(self, username, repository_name, pull_request_number, text, commit, file, line):
        self.bot.get_user(username).get_repo(repository_name).get_pull(pull_request_number).create_comment(text, commit,
                                                                                                           file, line)


class Reviewer:
    def __init__(self, requester, logger):
        self.requester = requester
        self.logger = logger

    def run_command(self, command):
        p = Popen(command, stdout=PIPE, stderr=STDOUT)
        result = ''
        for line in p.stdout.readlines():
            result += line.decode() + '\n'
        return result

    def get_repositories(self, username):
        self.logger.info("Obtaining of {0}'s repositories was started".format(username))
        repositories = self.requester.get_repositories(username)
        self.logger.info('Repositories was obtained')
        return repositories

    def create_pull_request_hook(self, username, repository_name, callback_url):
        self.logger.info('Setting of pull request web hook was started')
        self.requester.create_pull_request_hook(username, repository_name, callback_url)
        self.logger.info('Pull request web hook was successfully set')

    def delete_pull_request_hook(self, username, repository_name, callback_url):
        self.logger.info('Deleting of pull request web hook for repository {0}/{1} was started'.format(username,
                                                                                                       repository_name))
        self.requester.delete_pull_request_hook(username, repository_name, callback_url)
        self.logger.info('Pull request web hook for repository {0}/{1} was successfully deleted'.format(username,
                                                                                                        repository_name))

    def clone_repository(self, clone_url, save_path):
        self.logger.info('Repository cloning from {0} to {1} was started'.format(clone_url, save_path))
        if os.path.exists(save_path):
            self.logger.info('Directory {0} already exists. It will be deleted'.format(save_path))
            shutil.rmtree(save_path)
        bytes_io = io.BytesIO()
        self.requester.clone_repository(clone_url, save_path, bytes_io)
        self.logger.info(bytes_io.getvalue().decode())
        self.logger.info('Repository was cloned successfully')

    def get_file(self, file_url, save_path):
        self.logger.info('File downloading from {0} to {1} was started'.format(file_url, save_path))
        file = self.requester.get_file(file_url)
        self.logger.info('File {0} was downloaded successfully'.format(file_url))
        with open(save_path, 'w') as f:
            f.write(file.content.decode())
            self.logger.info('File {0} was saved successfully'.format(save_path))

    def apply_patch(self, repository_path, patch_path):
        self.logger.info('Applying of the patch was started')
        message = self.run_command([SETTINGS['apply'], repository_path, patch_path])
        self.logger.info('{0}\nApplying of the patch was completed'.format(message))

    def get_pull_request_and_latest_commit(self, username, repository_name, pull_request_number):
        self.logger.info('Obtaining of pull request with number {0} from repository {1}/{2} was started'.format(
            pull_request_number, username, repository_name))
        pull_request = self.requester.get_pull_request(username, repository_name, pull_request_number)
        self.logger.info('Pull request with name {0} was obtained\nObtaining of latest commit was started'
                         .format(pull_request.title))
        commit = self.requester.get_latest_commit_from_pull_request(pull_request)
        self.logger.info('Commit with sha {0} was obtained'.format(commit.sha))
        return pull_request, commit

    def review_pull_request(self, metrics, repository_path, diff_path, commit, username, repository_name,
                            pull_request_number):
        self.logger.info('Review was started')
        self.requester.create_status(commit, 'pending', SETTINGS['url'], 'Review was started', SETTINGS['name'])
        analyzer = Analyzer(metrics)
        counter = Counter()
        with open(os.path.join(repository_path, diff_path), 'r') as f:
            patch_set = PatchSet(f)
        sent_inspection_count = 0
        sent_inspections = {}
        for patch in patch_set:
            file_metrics = counter.metrics_for_file(os.path.join(repository_path, patch.path), verbose=True)
            self.logger.info('Here are metrics for file {0}: {1}'.format(patch.path, file_metrics))
            inspections = analyzer.inspect(file_metrics)
            first_line_in_diff = patch[0][0].diff_line_no
            for hunk in patch:
                self.logger.info('Here are inspections for file {0}: {1}'.format(patch.path, inspections))
                for metric_name, inspection_value in inspections.items():
                    for inspection, value in inspection_value.items():
                        self.logger.info('Inspection {0} has value {1}'.format(inspection, value))
                        if inspection in sent_inspections:
                            continue
                        elif 'lines' not in value:
                            sent_inspections[inspection] = True
                            self.logger.info('Issuing comment {0} for file {1}'.format(value['message'], patch.path))
                            self.requester.create_issue_comment_bot(username, repository_name, pull_request_number,
                                                                '{0}:\n{1}'.format(patch.path, value['message']))
                            sent_inspection_count += 1
                        else:
                            for line in value['lines']:
                                if hunk.target_start <= line <= hunk.target_start + hunk.target_length:
                                    # 3 is offset for unidiff hunk header
                                    hunk_line = line - hunk.target_start + 3
                                    try:
                                        line_object = hunk[hunk_line]
                                        target_line = line_object.diff_line_no - first_line_in_diff
                                        self.logger.info('Line with number {0} and value {1} was calculated\n'
                                                         'File {2} was commented on line {3} with message {4}\n'
                                                         'Hunk is from line {5} to line {6}'
                                                         .format(line_object.diff_line_no, line_object.value, patch.path,
                                                                 line, value['message'], hunk.target_start,
                                                                 hunk.target_start + hunk.target_length))
                                        self.requester.create_comment_bot(username, repository_name, pull_request_number,
                                                                          value['message'], commit, patch.path, target_line)
                                        sent_inspection_count += 1
                                    except Exception as e:
                                        self.logger.info('Hunk processing failed with exception {0} for hunk line {1}'
                                                         '(source length {2}, target length {3})'
                                                         .format(e, hunk_line, len(hunk.source), len(hunk.target)))
        if sent_inspection_count == 0:
            self.requester.create_status(commit, 'success', SETTINGS['url'], 'Review was completed. No issues found',
                                         SETTINGS['name'])
        else:
            self.requester.create_status(commit, 'error', SETTINGS['url'], 'Review was completed. Found some issues',
                                         SETTINGS['name'])
        self.logger.info('Review was completed. {0} issues found'.format(sent_inspection_count))

    def path_basename(self, path):
        return os.path.basename(os.path.normpath(path))

    def handle_hook(self, username, pull_request_number, metrics, base_path, clone_url, patch_url, diff_url):
        self.logger.info('Handling of hook for repository {0} was started'.format(clone_url))
        repository_name = os.path.splitext(self.path_basename(clone_url))[0]
        repository_path = os.path.join(base_path, repository_name)
        self.clone_repository(clone_url, repository_path)
        patch_path = os.path.join(repository_path, self.path_basename(patch_url))
        self.get_file(patch_url, patch_path)
        self.apply_patch(repository_path, patch_path)
        diff_path = os.path.join(repository_path, self.path_basename(diff_url))
        self.get_file(diff_url, diff_path)
        pull_request, commit = self.get_pull_request_and_latest_commit(username, repository_name, pull_request_number)
        self.review_pull_request(metrics, repository_path, diff_path, commit, username, repository_name,
                                 pull_request_number)
        self.logger.info('Hook for repository {0} was successfully processed'.format(clone_url))
