import os
from github import Github
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from bs4 import BeautifulSoup

# GitHub token for authentication
token = os.environ["GH_TOKEN"]
g = Github(token)

user = g.get_user("axif0")

# Collect basic stats
repos = [r for r in user.get_repos() if not r.fork]
total_stars = sum(r.stargazers_count for r in repos)
total_forks = sum(r.forks_count for r in repos)
contributors = set()

for repo in repos:
    try:
        contributors.update(c.login for c in repo.get_contributors())
    except:
        pass

# Get Codeforces stats
def get_codeforces_stats():
    try:
        # Fetch Codeforces profile page
        response = requests.get('https://codeforces.com/profile/asif2001')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the problems solved count
        info_blocks = soup.find_all('div', class_='_UserActivityFrame_counterValue')
        problems_solved = 0
        if info_blocks:
            # The first block typically contains problems solved
            problems_text = info_blocks[0].get_text().strip()
            problems_solved = int(''.join(filter(str.isdigit, problems_text)))
        
        # Get daily solved problems from a file
        daily_solved_file = ".github/data/cf_daily_solved.txt"
        today = datetime.utcnow().strftime('%Y-%m-%d')
        daily_solved = 0
        last_date = None
        
        os.makedirs(os.path.dirname(daily_solved_file), exist_ok=True)
        
        if os.path.exists(daily_solved_file):
            with open(daily_solved_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_date, count = lines[-1].strip().split(',')
                    if last_date == today:
                        daily_solved = int(count)
        
        # If it's a new day, reset the counter
        if last_date != today:
            daily_solved = 0
            
        # Calculate remaining problems and punishment
        DAILY_QUOTA = 2
        remaining = max(0, DAILY_QUOTA - daily_solved)
        punishment = remaining if datetime.utcnow().hour >= 23 else 0  # Check if day is almost over
        
        return {
            'total_solved': problems_solved,
            'daily_solved': daily_solved,
            'remaining': remaining,
            'punishment': punishment
        }
    except Exception as e:
        print(f"Error fetching Codeforces stats: {e}")
        return {
            'total_solved': 0,
            'daily_solved': 0,
            'remaining': 2,
            'punishment': 0
        }

# Get monthly contributions to new organizations
def get_monthly_org_contributions():
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    # Get all PRs created in the last month
    monthly_prs = g.search_issues(f'author:axif0 type:pr created:>={month_start.strftime("%Y-%m-%d")}')
    org_stats = defaultdict(lambda: {'success': 0, 'failed': 0})
    
    for pr in monthly_prs:
        if hasattr(pr, 'base'):  # Check if it's a PR
            org_name = pr.base.repo.organization.login if pr.base.repo.organization else pr.base.repo.owner.login
            if pr.state == 'closed' and pr.merged:
                org_stats[org_name]['success'] += 1
            elif pr.state == 'closed' and not pr.merged:
                org_stats[org_name]['failed'] += 1
            
    return org_stats

# Get weekly PR metrics
def get_weekly_pr_metrics():
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    
    # Get all PRs created in the last week
    weekly_prs = g.search_issues(f'author:axif0 type:pr created:>={week_start.strftime("%Y-%m-%d")}')
    success_count = 0
    failed_count = 0
    
    for pr in weekly_prs:
        if hasattr(pr, 'base'):  # Check if it's a PR
            if pr.state == 'closed' and pr.merged:
                success_count += 1
            elif pr.state == 'closed' and not pr.merged:
                failed_count += 1
            
    return success_count, failed_count

# Get the new metrics
monthly_org_stats = get_monthly_org_contributions()
weekly_success, weekly_failed = get_weekly_pr_metrics()
cf_stats = get_codeforces_stats()

# Set goals
MONTHLY_ORG_GOAL = 2  # At least 2 successful contributions to new orgs per month
WEEKLY_PR_GOAL = 2    # At least 2 PRs per week

# Calculate goal achievements
total_monthly_success = sum(stats['success'] for stats in monthly_org_stats.values())
monthly_goal_achieved = total_monthly_success >= MONTHLY_ORG_GOAL
weekly_goal_achieved = (weekly_success + weekly_failed) >= WEEKLY_PR_GOAL

# Create the Codeforces section
cf_section = f"\n### Codeforces Progress\n"
cf_section += f"- Total problems solved: {cf_stats['total_solved']}\n"
cf_section += f"- Today's progress: {cf_stats['daily_solved']}/2 problems\n"
if cf_stats['punishment'] > 0:
    cf_section += f"- 🔴 Punishment: {cf_stats['punishment']} problems pending from today's quota\n"
elif cf_stats['remaining'] > 0:
    cf_section += f"- ⚠️ Remaining today: {cf_stats['remaining']} problems\n"
else:
    cf_section += f"- ✅ Daily quota completed!\n"

# Create the monthly org contributions section
monthly_org_section = f"\n### Monthly Organizations Goal {'Achieved 🟢' if monthly_goal_achieved else 'Failed 🔴'}\n"
monthly_org_section += f"Goal: {MONTHLY_ORG_GOAL} successful contributions\n"
for org, stats in monthly_org_stats.items():
    monthly_org_section += f"- {org}: 🟢 {stats['success']} merged | 🔴 {stats['failed']} closed\n"
monthly_org_section += f"Total successful contributions: {total_monthly_success}\n"

# Create the weekly PR section
weekly_pr_section = f"\n### Weekly Pull Requests Goal {'Achieved 🟢' if weekly_goal_achieved else 'Failed 🔴'}\n"
weekly_pr_section += f"Goal: {WEEKLY_PR_GOAL} pull requests per week\n"
weekly_pr_section += f"- 🟢 {weekly_success} successfully merged\n"
weekly_pr_section += f"- 🔴 {weekly_failed} closed without merging\n"
weekly_pr_section += f"Total PRs this week: {weekly_success + weekly_failed}\n"

stats_block = f""" GitHub Activity Summary (Updated Daily)

- Public repositories: {len(repos)}
- Total stars: {total_stars}
- Total forks: {total_forks}
- Contributors across repos: {len(contributors)}
{cf_section}
{monthly_org_section}
{weekly_pr_section}
- Last updated: {datetime.utcnow().strftime('%Y-%m-%d')}
"""

# Inject into README.md
readme_path = "README.md"
with open(readme_path, "r") as f:
    lines = f.readlines()

start, end = None, None
for i, line in enumerate(lines):
    if line.strip() == "<!-- STATS:START -->":
        start = i
    elif line.strip() == "<!-- STATS:END -->":
        end = i

if start is not None and end is not None:
    lines[start+1:end] = [stats_block + "\n"]

with open(readme_path, "w") as f:
    f.writelines(lines)