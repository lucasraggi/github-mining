from miner.issue_miner import IssueMiner


class GitHubMiner:

    def __init__(self, url, username, token, params):
        self.url = url
        self.username = username
        self.token = token
        self.params = params

    def mine_issues(self, issues_output, events_output, comments_output):

        # Mine GitHub closed issues
        mine_issues = IssueMiner(self.url, issues_output, events_output, comments_output, self.username, self.token, self.params)
        mine_issues.mine_issues()
       #  mine_issues.mine_issues_events()

    # def mine_pr(self, pr_output):
    #
    #     # Mine GitHub closed pull-requests
    #     mine_prs = pr_miner.PullRequestMiner(self.url, pr_output, self.username, self.token)
    #     mine_prs.mine_prs()