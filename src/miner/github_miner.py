from miner.issue_miner import IssueMiner
from miner.pr_miner import PullRequestMiner


class GitHubMiner:

    def __init__(self, url, username, token, params):
        self.url = url
        self.username = username
        self.token = token
        self.params = params

    def mine_issues(self, issues_output, issues_events_output, issues_comments_output, mine_data_output):

        # Mine GitHub closed issues
        mine_issues = IssueMiner(self.url, issues_output, issues_events_output, issues_comments_output, self.username, self.token, self.params, mine_data_output)
        #mine_issues.mine_issues()
        mine_issues.mine_data_from_json(issues_output, issues_events_output, issues_comments_output, mine_data_output)

    def mine_prs(self, pr_output, pr_events_output, pr_comments_output, pr_reviewers_output, mine_data_output):

        # Mine GitHub closed pull-requests
        mine_prs = PullRequestMiner(self.url, pr_output, pr_events_output, pr_comments_output, pr_reviewers_output, self.username, self.token, self.params, mine_data_output)
        #mine_prs.mine_prs()
        mine_prs.mine_data_from_json(pr_output, pr_events_output, pr_comments_output, mine_data_output)
