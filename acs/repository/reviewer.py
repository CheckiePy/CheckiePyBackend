import os
import io
import shutil
import porcelain
import requests

from github import Github


class Logger:
    def info(self, text):
        print(text)


class Reviewer:
    def __init__(self, access_token, logger):
        self.access_token = access_token
        self.github = Github(self.access_token)
        self.logger = logger

    # def run_command(command):
    #     p = Popen(command, stdout=PIPE, stderr=STDOUT)
    #     result = ''
    #     for line in p.stdout.readlines():
    #         result += line.decode() + '\n'
    #     return result

    def load_repositories(self, username):
        repositories = self.github.get_user(username).get_repos()
        for repository in repositories:
            # user, name
            print(repository)

    def create_pull_hook(self, username, repository_name, callback_url):
        github_repository = self.github.get_user(username).get_repo(repository_name)
        github_repository.create_hook('web', {'url': callback_url, 'content_type': 'json'}, ['pull_request'], True)

    #
    #
    # def is_need_to_handle_hook(body):
    #     # We need to check repo only if pull request is newly created or received a new commit.
    #     if ACTION in body and (body[ACTION] == OPENED or body[ACTION] == SYNCHRONIZE):
    #         return True
    #     return False
    #
    #

    def clone_repository(self, clone_url, save_path):
        self.logger.info('Repository cloning from {0} to {1} started'.format(clone_url, save_path))

        if os.path.exists(save_path):

            self.logger.info('Directory {0} already exists. It will be deleted'.format(save_path))

            shutil.rmtree(save_path)

        bytes_io = io.BytesIO()
        porcelain.clone(clone_url, save_path, errstream=bytes_io)

        self.logger.info(bytes_io.getvalue().decode())
        self.logger.info('Repository was cloned successfully')

    def load_file(self, file_url, save_path):
        self.logger.info('File downloading from {0} to {1} started'.format(file_url, save_path))

        file = requests.get(file_url)

        self.logger.info('File {0} was downloaded successfully'.format(file_url))

        with open(save_path, 'w') as f:
            f.write(file.content.decode())

            self.logger.info('File {0} was saved successfully'.format(save_path))

    #
    # def apply_patch(repo_path):
    #     logger.info('Applying the patch')
    #
    #     # Todo: pass patch filename as argument
    #     message = run_command(["{0}/bash/applypatch.sh".format(settings.BASE_DIR), repo_path])
    #
    #     logger.info(message)
    #
    #
    #
    # def access_to_repo_as_bot(body, bot_name):
    #     repo_name = body[REPOSITORY][NAME]
    #     owner = body[REPOSITORY][OWNER][LOGIN]
    #
    #     logger.info('Trying to get access to {0} repo of {1} with bot {2}'.format(repo_name, owner, bot_name))
    #
    #     github = Github(config.BOT_AUTH)
    #     github_user = github.get_user(owner)
    #     github_repo = github_user.get_repo(repo_name)
    #
    #     logger.info('Access successfully gained')
    #
    #     return github_repo
    #
    #
    # def get_pull_request_and_latest_commit(body, github_repo):
    #     pull_request = github_repo.get_pull(body[NUMBER])
    #
    #     logger.info('Got pull request with titile {0} and number {1}'.format(pull_request.title, pull_request.number))
    #
    #     # Todo: check if comment to latest commit is ok when style violation in previous commit
    #     commit = pull_request.get_commits().reversed[0]
    #
    #     logger.info('Got commit with sha {0}'.format(commit.sha))
    #
    #     return pull_request, commit
    #
    #
    # def review_repo(repository_id, repo_path, pull_request, commit):
    #     logger.info('Starting review')
    #
    #     commit.create_status('pending', 'http://acs.uplatform.ru/', 'Review started.', 'acs')
    #
    #     # Todo: refactor
    #     connection = models.GitRepositoryConnection.objects.get(repository=repository_id)
    #     repo_metrics = json.loads(connection.code_style.metrics)
    #     analyzer = Analyzer(repo_metrics)
    #     counter = Counter()
    #     with open(os.path.join(repo_path, DIFF_FILENAME), 'r') as d:
    #         patch_set = PatchSet(d)
    #
    #     comments_sent = 0
    #
    #     mentioned = {}
    #     for patch in patch_set:
    #         file_metrics = counter.metrics_for_file(os.path.join(repo_path, patch.path), verbose=True)
    #
    #         logger.info('Metrics for file {0} {1}'.format(patch.path, file_metrics))
    #
    #         inspections = analyzer.inspect(file_metrics)
    #         first_line_in_diff = patch[0][0].diff_line_no
    #         for hunk in patch:
    #
    #             logger.info('Inspections for file {0} {1}'.format(patch.path, inspections))
    #
    #             for metric_name, inspection_value in inspections.items():
    #                 for inspection, value in inspection_value.items():
    #
    #                     logger.info('Inspection {0} has value {1}'.format(inspection, value))
    #
    #                     if inspection in mentioned:
    #                         continue
    #                     elif 'lines' not in value:
    #                         mentioned[inspection] = True
    #
    #                         logger.info('Issue comment {0} to file {1}'.format(value['message'], patch.path))
    #
    #                         pull_request.create_issue_comment('{0}:\n{1}'.format(patch.path, value['message']))
    #                         comments_sent += 1
    #                     else:
    #                         for line in value['lines']:
    #                             if hunk.target_start <= line <= hunk.target_start + hunk.target_length:
    #
    #                                 line_object = hunk[line - hunk.target_start + 3]
    #                                 target_line = line_object.diff_line_no - first_line_in_diff
    #
    #                                 logger.info('Calculated line with #{0} and value {1}'.format(line_object.diff_line_no, line_object.value))
    #                                 logger.info('Comment file {0} on line {1} with message {2}'.format(patch.path, line, value['message']))
    #                                 logger.info('Hunk from {0} to {1}'.format(hunk.target_start, hunk.target_start + hunk.target_length))
    #
    #                                 pull_request.create_comment(value['message'], commit, patch.path, target_line)
    #                                 comments_sent += 1
    #     if comments_sent == 0:
    #         pull_request.create_issue_comment('Repository was reviewed. Everything is alright')
    #         commit.create_status('success', 'http://acs.uplatform.ru/', 'Review completed. No issue found.', 'acs')
    #
    #         logger.info('Everything is alrigth')
    #     else:
    #         commit.create_status('error', 'http://acs.uplatform.ru/', 'Review completed. Found some issues.', 'acs')
    #
    #
    # @shared_task
    # def handle_hook(json_body, repository_id):
    #
    #     print(logger)
    #
    #     try:
    #         body = json.loads(json_body)
    #
    #         if not is_need_to_handle_hook(body):
    #             return
    #
    #         logger.info('Started review for repo id {0}'.format(repository_id))
    #
    #         repo_path = clone_repo(body)
    #         save_patch(body, repo_path)
    #         apply_patch(repo_path)
    #         save_diff(body, repo_path)
    #
    #         github_repo = access_to_repo_as_bot(body, BOT_NAME)
    #         pull_request, commit = get_pull_request_and_latest_commit(body, github_repo)
    #
    #         # Todo: record mentioned violations
    #         review_repo(repository_id, repo_path, pull_request, commit)
    #
    #         shutil.rmtree(repo_path)
    #
    #         logger.info('Repo {0} review successfully completed'.format(repository_id))
    #     except Exception as e:
    #         logger.exception(e)
