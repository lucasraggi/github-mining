from optparse import OptionParser
from miner.github_miner import GitHubMiner

# Create the CLI parser
usage = "usage: %prog [options] arg"
parser = OptionParser()

# Add the available options to the parser
parser.add_option("-u", "--url", dest="url",  help="GitHub repository URL in format :user/:repository")
parser.add_option("-p", "--path", dest="path", help="Path to the git repository")
parser.add_option("--issues_output", dest="issues_output", help="Path to the Issues output directory")
parser.add_option("--events_output", dest="events_output", help="Path to the Issues events output directory")
parser.add_option("--comments_output", dest="comments_output", help="Path to the Issues comments output directory")
parser.add_option("--pr_output", dest="pr_output", help="Path to the Pull Requests output directory")
parser.add_option("--username", dest="username", help="The GitHub username for authentication")
parser.add_option("--token", dest="token", help="The GitHub token for authentication")
parser.add_option("--params", dest="params", help="The GitHub params in format: {'param1': 'value1', 'param2': 'value2, ...'}")

# Parse the CLI args
(options, args) = parser.parse_args()


# Start GitHub mining
miner = GitHubMiner(options.url, options.username, options.token, options.params)
miner.mine_issues(options.issues_output, options.events_output, options.comments_output)
# miner.mine_pr(options.pr_output)
