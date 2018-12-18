import requests
import logging

# TODO
# Make requests of comments and events from the entire repo instead of making requests for each issue
# Save data collected to a csv or database
# Refactor functions with objects to simplify parameters


def get_comment_from_issue(issue, params, username, token):
    comment_res = requests.get(issue['comments_url'], params=params, auth=(username, token))
    if comment_res.ok:
        comments = comment_res.json()
        print('     Comments from: ' + str(issue['id']))
        for comment in comments:
            print('             Comment ID: ' + str(comment['id']))
    else:
        logging.warning(str(comment_res.status_code))


# Return False if issue does not have a closed event
# Return login of the person who closed the issue if the issue has a closed event
def is_event_closed(issue, params, username, token):
    event_res = requests.get(issue['events_url'], params=params, auth=(username, token))
    if event_res.ok:
        events = event_res.json()
        for event in events:
            if event['event'] == 'closed':
                return event['actor']['login']
        return False
    else:
        logging.warning(str(event_res.status_code))


# Get issues from all pages from selected repository
def get_all_pages(res, issues, params, username, token):
    count = 0
    while 'next' in res.links.keys():
        logging.info('Retrieving page ' + count)
        res = requests.get(res.links['next']['url'], params=params, auth=(username, token))
        issues.extend(res.json())
        count += 1
    return issues


# Get comments from issues with the word "bug" in the label
def get_all_bug_issues(issues, params, username, token):
    for issue in issues:
        for label in issue['labels']:
            closed_by = is_event_closed(issue, params, username, token) #
            if label['name'].find("bug") != -1 and closed_by is not False:
                print('Issue title: ' + issue['title'])
                print('     Opened By: ' + issue['user']['login'])
                print('     Closed By: ' + closed_by)
                print('     State: ' + issue['state'])
                print('     State Label: ' + label['name'])
                get_comment_from_issue(issue, params, username, token)


# Debug function to match issues from web clients not including pull requests
def get_all_issues_debug(issues, params, username, token):
    for issue in issues:
        for label in issue['labels']:
            closed_by = is_event_closed(issue, params, username, token)
            if 'pull_request' not in issue and closed_by is not False:
                print('Issue title: ' + issue['title'])
                print('     Opened By: ' + issue['user']['login'])
                print('     Closed By: ' + closed_by)
                print('     State: ' + issue['state'])
                print('     State Label: ' + label['name'])
                get_comment_from_issue(issue, params, username, token)


def main():
    url = 'https://api.github.com/repos/spring-projects/spring-boot/issues'
    params = {'state': 'closed', 'per_page': '100'}

    username = 'lucas.raggi@hotmail.com'
    token = '232d08ee5274613f1d8f063abaa7fded8656fd6b' # Token with permission only for requests

    res = requests.get(url, params=params, auth=(username, token))
    if res.ok:
        issues = res.json()
        # issues = get_all_pages(res, issues, params, username, token)
        # get_all_issues_debug(issues, params, username, token)
        get_all_bug_issues(issues, params, username, token)
    else:
        logging.warning(str(res.status_code))


main()
