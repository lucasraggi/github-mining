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


class PullRequestMiner:

    def __init__(self, url, pr_output_path, pr_events_output_path, pr_comments_output_path, pr_reviewers_output_path, username, token, params):
        self.url = url
        self.prs_output_path = pr_output_path
        self.comments_output_path = pr_events_output_path
        self.events_output_path = pr_comments_output_path
        self.reviewers_output_path = pr_reviewers_output_path
        self.username = username
        self.token = token
        self.params = literal_eval(params)

        self.pull_requests = {}
        self.pull_requests_numbers = []
        self.pull_requests_issues = {}
        self.pull_requests_events = {}
        self.pull_requests_comments = {}
        self.base_url = 'https://api.github.com/repos/'

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
        for pr in prs:
            pr_issue = self.get_json_from_key(pr, 'issue_url')
            print('issue: ', pr_issue['title'])
            for label in pr_issue['labels']:
                if label['name'].find("bug") != -1 and self.is_issue_closed(pr_issue):
                    print("got in: ",  pr_issue['title'])
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

    def mine_prs(self):
        res_url = self.base_url + self.url + "/pulls"
        res = requests.get(res_url, params=self.params, auth=(self.username, self.token))
        if res.ok:
            prs = res.json()
            # prs = self.get_all_pages(res, prs)
            self.get_all_prs(prs)
        else:
            logging.warning(str(res.status_code))






