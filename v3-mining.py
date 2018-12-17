import requests
import json


def get_all_bug_issues(issues):
    for issue in issues:
        if 'pull_request' not in issue:
            for label in issue['labels']:
                if label['name'].find("bug") != -1:
                    print(issue['title'])
                    print("State: " + issue['state'])
                    print("     " + label['name'])


def get_all_issues(issues):
    count = 1
    for issue in issues:
        print(str(count) + '- ' + issue['title'])
        count += 1


def main():
    url = 'https://api.github.com/repos/spring-projects/spring-boot/issues'
    params = {'state': 'closed', 'page': '0', 'per_page': '100'}
    r = requests.get(url, params=params)
    link = r.headers.get('link', None)
    while link is not None:
        print(link)
        print('-------------------------------------------------')
        r = requests.get(url)
        link = r.headers.get('link', None)
        url = link.split(">")[0][1:]
    #issues = r.json()
    #get_all_issues(issues)


main()

