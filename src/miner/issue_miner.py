import errno
import json
import os
from ast import literal_eval
import requests
import logging

# TODO
# Make requests of comments and events from the entire repo instead of making requests for each issue
# Save data collected to a csv or database
# Refactor functions with objects to simplify parameters
import tqdm as tqdm


class IssueMiner:

    def __init__(self, url, issues_output_path, issues_events_output_path, issues_comments_output_path, username, token, params, mine_data_output):
        self.url = url
        self.issues_output_path = issues_output_path
        self.comments_output_path = issues_comments_output_path
        self.events_output_path = issues_events_output_path
        self.username = username
        self.token = token
        self.params = literal_eval(params)
        self.mine_data_output_path = mine_data_output

        self.closed_issues = {}
        self.closed_issues_numbers = []
        self.closed_issues_events = {}
        self.closed_issues_comments = {}
        self.base_url = 'https://api.github.com/repos/'

        self.mine_data = {}

    def save_json(self, json_type):
        path, json_list = self.path_and_data_by_type(json_type)

        try:
            os.makedirs(path)
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

        os.chdir(path)
        for number in tqdm.tqdm(self.closed_issues_numbers):
            number = str(number)
            json_data = json_list[number]
            with open(number + '.json', 'w') as output_file:
                json.dump(json_data, output_file)
        os.chdir("..")

    def path_and_data_by_type(self, json_type):
        if json_type == 'issues':
            return self.issues_output_path, self.closed_issues
        if json_type == 'events':
            return self.events_output_path, self.closed_issues_events
        if json_type == 'comments':
            return self.comments_output_path, self.closed_issues_comments

    def get_key_from_issue(self, issue, key):
        key_res = requests.get(issue[key], params=self.params, auth=(self.username, self.token))
        if key_res.ok:
            keys = key_res.json()
            keys = self.get_all_pages(key_res, keys)
            return keys
        else:
            logging.warning(str(key_res.status_code))

    # Get issues from all pages from selected repository
    def get_all_pages(self, res, json_list):
        count = 0
        while 'next' in res.links.keys():
            logging.info('Retrieving page ', count)
            res = requests.get(res.links['next']['url'], params=self.params, auth=(self.username, self.token))
            json_list.extend(res.json())
            count += 1
        return json_list

    def is_issue_closed(self, issue):
        closed_count = 0
        reopened_count = 0
        event_res = requests.get(issue['events_url'], params=self.params, auth=(self.username, self.token))
        if event_res.ok:
            events = event_res.json()
            for event in events:
                if event['event'] == 'closed':
                    closed_count += 1
                if event['event'] == 'reopened':
                    reopened_count += 1
            if closed_count > reopened_count:
                return True
            return False
        else:
            logging.warning(str(event_res.status_code))

    def get_all_issues(self, issues):
        logging.info('Mining issues, events and comments...')
        print('Mining issues, events and comments...')
        for issue in tqdm.tqdm(issues):
            for label in issue['labels']:
                if 'pull_request' not in issue and label['name'].find("bug") != -1 and self.is_issue_closed(issue):
                    issue_events = self.get_key_from_issue(issue, 'events_url')
                    issue_comments = self.get_key_from_issue(issue, 'comments_url')

                    self.closed_issues_numbers.append(issue['number'])
                    self.closed_issues[str(issue['number'])] = issue
                    self.closed_issues_events[str(issue['number'])] = issue_events
                    self.closed_issues_comments[str(issue['number'])] = issue_comments
        logging.info('Github issues, events and comments successfully mined...')
        print('Github issues, events and comments successfully mined...')
        self.save_json('issues')
        self.save_json('events')
        self.save_json('comments')
        logging.info('Github issues, events and comments successfully mined...')
        print('Github issues, events and comments successfully writen...')

    def mine_issues(self):
        res_url = self.base_url + self.url + "/issues"
        res = requests.get(res_url, params=self.params, auth=(self.username, self.token))
        if res.ok:
            issues = res.json()
            issues = self.get_all_pages(res, issues)
            self.get_all_issues(issues)
        else:
            logging.warning(str(res.status_code))


    def mine_open_event(self, pr_output_path):

        # Mine open event
        issue_files = os.listdir(pr_output_path)

        for issue_json in issue_files:
            id = issue_json.split('.')
            with open(pr_output_path + '/' + issue_json, 'r') as json_file:
                issue_data = json.load(json_file)

                # Creating reference to the pull request by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Saving the autor of the issues/PR by ID:
                self.mine_data[id[0]]['opened_by'] = issue_data['user']['login']

    # Mine close event
    def mine_close_event(self, issue_events_output):
        # Getting all events file in dir:
        pr_files = os.listdir(issue_events_output)

        for pr_json in pr_files:
            id = pr_json.split('.')
            with open(issue_events_output + '/' + pr_json, 'r') as json_file:
                issue_data = json.load(json_file)

                # Creating reference to the issue by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Iterating over the events in issue:
                for issue_event in issue_data:
                    if issue_event['event'] == 'closed':
                        # Saving the autor of the CLOSE event by ID:
                        self.mine_data[id[0]]['closed_by'] = issue_event['actor']['login']

    def mine_comments(self, issue_comments_output):
        # Getting all events file in dir:
        issue_files = os.listdir(issue_comments_output)

        for issue_json in issue_files:
            id = issue_json.split('.')
            with open(issue_comments_output + '/' + issue_json, 'r') as json_file:
                issue_comment_data = json.load(json_file)

                # Creating reference to the issue by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Iterating over the comments in issue:
                self.mine_data[id[0]]['comments'] = []
                for issue_comment in issue_comment_data:
                    # Saving all body of the commments on this issue/PR:
                    self.mine_data[id[0]]['comments'].append(issue_comment)

    def mine_data_from_json(self, issues_output, issue_events_output, issue_comments_output, mine_data_output):
        self.mine_open_event(issues_output)
        self.mine_close_event(issue_events_output)
        self.mine_comments(issue_comments_output)

        if not os.path.exists(mine_data_output):
            os.makedirs(mine_data_output)

        with open(mine_data_output + '/issue_mined_data.json', 'w') as output_file:
            json.dump(self.mine_data, output_file)

        print('Mined issue data was successfully writen...')
