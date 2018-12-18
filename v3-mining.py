import requests
import json
import logging


def get_comment_from_issue(issue, params, username, token):
    comment_res = requests.get(issue['comments_url'], params=params, auth=(username, token))
    comments = comment_res.json()
    print('     Comments from ' + issue['title'])
    for comment in comments:
        print('             Comment ID: ' + str(comment['id']))


def is_event_closed(issue, params, username, token):
    event_res = requests.get(issue['events_url'], params=params, auth=(username, token))
    events = event_res.json()
    for event in events:
        if event['event'] == 'closed':
            return True
    return False


def get_all_pages(res, issues, params, username, token):
    count = 0
    while 'next' in res.links.keys():
        logging.info('Retrieving page ' + count)
        res = requests.get(res.links['next']['url'], params=params, auth=(username, token))
        issues.extend(res.json())
        count += 1
    return issues


def get_all_bug_issues(issues, params, username, token):
    for issue in issues:
        for label in issue['labels']:
            if label['name'].find("bug") != -1 and is_event_closed(issue, params, username, token):
                print('Issue title: ' + issue['title'])
                print("State: " + issue['state'])
                print("     State Label: " + label['name'])
                get_comment_from_issue(issue, params, username, token)


def get_all_issues(issues, params, username, token):
    count = 1
    for issue in issues:
        print(str(count) + '- ' + issue['title'])
        print('     ' + issue['events_url'])
        print('-----------------------------------')
        count += 1


def main():
    url = 'https://api.github.com/repos/spring-projects/spring-boot/issues'
    params = {'state': 'closed', 'per_page': '100'}

    username = 'lucas.raggi@hotmail.com'
    token = '232d08ee5274613f1d8f063abaa7fded8656fd6b'

    res = requests.get(url, params=params, auth=(username, token))
    if res.ok:
        issues = res.json()
        # issues = get_all_pages(res, issues, params, username, token)
        # get_all_issues(issues, params, username, token)
        get_all_bug_issues(issues, params, username, token)
    else:
        logging.warning(str(res.status_code))


main()