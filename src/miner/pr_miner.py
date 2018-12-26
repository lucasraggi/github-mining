import errno
import json
import os
from ast import literal_eval
import requests
import logging

import tqdm as tqdm

class PullRequestMiner:

    def __init__(self, url, pr_output_path, pr_events_output_path, pr_comments_output_path, pr_reviewers_output_path, username, token, params, mine_data_output):
        self.url = url
        self.prs_output_path = pr_output_path
        self.comments_output_path = pr_comments_output_path
        self.events_output_path = pr_events_output_path
        self.reviewers_output_path = pr_reviewers_output_path
        self.username = username
        self.token = token
        self.params = literal_eval(params)
        self.mine_data_output_path = mine_data_output

        self.pull_requests = {}
        self.pull_requests_numbers = []
        self.pull_requests_issues = {}
        self.pull_requests_events = {}
        self.pull_requests_comments = {}
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
        for number in tqdm.tqdm(self.pull_requests_numbers):
            number = str(number)
            json_data = json_list[number]
            with open(number + '.json', 'w') as output_file:
                json.dump(json_data, output_file)
        os.chdir("..")

    def path_and_data_by_type(self, json_type):
        if json_type == 'pull_requests':
            return self.prs_output_path, self.pull_requests_issues
        if json_type == 'events':
            return self.events_output_path, self.pull_requests_events
        if json_type == 'comments':
            return self.comments_output_path, self.pull_requests_comments
        if json_type == 'reviews':
            return self.reviewers_output_path, self.pull_requests

    def get_json_from_key(self, source, key):
        key_res = requests.get(source[key], params=self.params, auth=(self.username, self.token))
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
            events = self.get_all_pages(event_res, events)
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

    def get_all_prs(self, prs):
        logging.info('Mining pull requests, events and comments...')
        print('Mining pull requests, events and comments...')
        for pr in tqdm.tqdm(prs):
            pr_issue = self.get_json_from_key(pr, 'issue_url')
            for label in pr_issue['labels']:
                if label['name'].find("bug") != -1 and self.is_issue_closed(pr_issue):
                    pr_events = self.get_json_from_key(pr_issue, 'events_url')
                    pr_comments = self.get_json_from_key(pr_issue, 'comments_url')

                    self.pull_requests_numbers.append(pr_issue['number'])
                    self.pull_requests[str(pr_issue['number'])] = pr
                    self.pull_requests_issues[str(pr_issue['number'])] = pr_issue
                    self.pull_requests_events[str(pr_issue['number'])] = pr_events
                    self.pull_requests_comments[str(pr_issue['number'])] = pr_comments
        logging.info('Github pull requests, events and comments successfully mined...')
        print('Github pull requests, events and comments successfully mined...')
        self.save_json('pull_requests')
        self.save_json('events')
        self.save_json('comments')
        self.save_json('reviews')
        logging.info('Github pull requests, events and comments successfully mined...')
        print('Github pull requests, events and comments successfully writen...')

    def mine_prs(self):
        res_url = self.base_url + self.url + "/pulls"
        res = requests.get(res_url, params=self.params, auth=(self.username, self.token))
        if res.ok:
            prs = res.json()
            prs = self.get_all_pages(res, prs)
            self.get_all_prs(prs)
        else:
            logging.warning(str(res.status_code))

    def mine_open_event(self, pr_output_path):

        # Mine open event
        pr_files = os.listdir(pr_output_path)

        for pr_json in pr_files:
            id = pr_json.split('.')

            with open(pr_output_path + '/' + pr_json, 'r') as json_file:
                pr_data = json.load(json_file)

                # Creating reference to the pull request by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Saving the autor of the issues/PR by ID:
                self.mine_data[id[0]]['opened_by'] = pr_data['user']['login']

    # Mine close event
    def mine_close_event(self, pr_events_output):
        # Getting all events file in dir:
        pr_files = os.listdir(pr_events_output)

        for pr_json in pr_files:
            id = pr_json.split('.')
            with open(pr_events_output + '/' + pr_json, 'r') as json_file:
                pr_data = json.load(json_file)

                # Creating reference to the pull request by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Iterating over the events in PR:
                for pr_event in pr_data:
                    if pr_event['event'] == 'closed':
                        # Saving the autor of the CLOSE event by ID:
                        self.mine_data[id[0]]['closed_by'] = pr_event['actor']['login']

    def mine_comments(self, pr_comments_output):
        # Getting all events file in dir:
        pr_files = os.listdir(pr_comments_output)

        for pr_json in pr_files:
            id = pr_json.split('.')
            with open(pr_comments_output + '/' + pr_json, 'r') as json_file:
                pr_comment_data = json.load(json_file)

                # Creating reference to the pull request by ID:
                if id[0] not in self.mine_data:
                    self.mine_data[id[0]] = {}

                # Iterating over the comments in PR:
                self.mine_data[id[0]]['comments'] = []
                for pr_comment in pr_comment_data:
                    # Saving all body of the commments on this issue/PR:
                    self.mine_data[id[0]]['comments'].append(pr_comment)

    def mine_data_from_json(self, pr_output, pr_events_output, pr_comments_output, mine_data_output):
        self.mine_open_event(pr_output)
        self.mine_close_event(pr_events_output)
        self.mine_comments(pr_comments_output)

        if not os.path.exists(mine_data_output):
            os.makedirs(mine_data_output)

        with open(mine_data_output + '/PR_mined_data.json', 'w') as output_file:
            json.dump(self.mine_data, output_file)

        print('Mined PR data was successfully writen...')
