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

    def __init__(self, url, issues_output_path, issues_events_output_path, issues_comments_output_path, username, token, params):
        self.url = url
        self.issues_output_path = issues_output_path
        self.comments_output_path = issues_comments_output_path
        self.events_output_path = issues_events_output_path
        self.username = username
        self.token = token
        self.params = literal_eval(params)

        self.closed_issues = {}
        self.closed_issues_numbers = []
        self.closed_issues_events = {}
        self.closed_issues_comments = {}
        self.base_url = 'https://api.github.com/repos/'

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
            return keys
        else:
            logging.warning(str(key_res.status_code))

    # Get issues from all pages from selected repository
    def get_all_pages(self, res, issues):
        count = 0
        while 'next' in res.links.keys():
            logging.info('Retrieving page ', count)
            res = requests.get(res.links['next']['url'], params=self.params, auth=(self.username, self.token))
            issues.extend(res.json())
            count += 1
        return issues

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
        for issue in issues:
            # print('issue title: ', issue['title'])
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

    def mine_issues(self):
        res_url = self.base_url + self.url + "/issues"
        res = requests.get(res_url, params=self.params, auth=(self.username, self.token))
        if res.ok:
            issues = res.json()
            # issues = self.get_all_pages(res, issues)
            self.get_all_issues(issues)
        else:
            logging.warning(str(res.status_code))






