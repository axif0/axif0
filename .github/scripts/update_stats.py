import os
from github import Github
from datetime import datetime, timedelta
from collections import defaultdict
import requests
import json

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
        # Get submission history
        submissions_url = 'https://codeforces.com/api/user.status?handle=asif2001'
        submissions_response = requests.get(submissions_url)
        
        print(f"Debug - API Response Status: {submissions_response.status_code}")
        
        if submissions_response.status_code == 200:
            data = submissions_response.json()
            if data['status'] == 'OK':
                submissions = data['result']
                print(f"Debug - Total submissions found: {len(submissions)}")
                
                # Count unique solved problems
                solved_problems = set()
                today_solved = set()  # Track problems solved today
                today = datetime.utcnow().strftime('%Y-%m-%d')
                
                for sub in submissions:
                    try:
                        if sub['verdict'] == 'OK':  # Accepted submission
                            problem = sub['problem']
                            problem_key = f"{problem.get('contestId', '0')}-{problem.get('index', '0')}"
                            solved_problems.add(problem_key)
                            
                            # Check if solved today
                            sub_time = datetime.fromtimestamp(sub['creationTimeSeconds'])
                            if sub_time.strftime('%Y-%m-%d') == today:
                                today_solved.add(problem_key)
                    except Exception as e:
                        print(f"Debug - Error processing submission: {e}")
                        continue
                
                print(f"Debug - Unique problems solved: {len(solved_problems)}")
                print(f"Debug - Problems solved today: {len(today_solved)}")
                print(f"Debug - Sample problem keys: {list(solved_problems)[:5]}")
                
                # Get daily solved problems from a file
                daily_solved_file = ".github/data/cf_daily_solved.txt"
                daily_solved = len(today_solved)  # Use actual solved count for today
                
                # Create data directory if it doesn't exist
                os.makedirs(os.path.dirname(daily_solved_file), exist_ok=True)
                
                # Update the daily solved count file
                with open(daily_solved_file, 'w') as f:
                    f.write(f"{today},{daily_solved}\n")
                    
                # Calculate remaining problems and punishment
                DAILY_QUOTA = 2
                remaining = max(0, DAILY_QUOTA - daily_solved)
                punishment = remaining if datetime.utcnow().hour >= 23 else 0  # Check if day is almost over
                
                stats = {
                    'total_solved': len(solved_problems),
                    'daily_solved': daily_solved,
                    'remaining': remaining,
                    'punishment': punishment
                }
                
                print(f"Debug - Final stats: {stats}")
                return stats
        
        print(f"Error fetching Codeforces stats: API response {submissions_response.status_code}")
        return {
            'total_solved': 0,
            'daily_solved': 0,
            'remaining': 2,
            'punishment': 0
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

# Create sections with table layout
stats_block = f""" GitHub Activity Summary (Updated Daily)

- Public repositories: {len(repos)}
- Total stars: {total_stars}
- Total forks: {total_forks}
- Contributors across repos: {len(contributors)}

<div align="center">

<table>
<tr>
<td width="33%" align="center">

### 📊 Codeforces Progress
- Total problems solved: {cf_stats['total_solved']}
- Today's progress: {cf_stats['daily_solved']}/2 problems
{f"- 🔴 Punishment: {cf_stats['punishment']} problems pending" if cf_stats['punishment'] > 0 else ("- ✅ Daily quota completed!" if cf_stats['remaining'] == 0 else f"- ⚠️ Remaining today: {cf_stats['remaining']} problems")}

</td>
<td width="33%" align="center">

### 🌟 Monthly Organizations
**Goal Status: {' 🟢 Achieved' if monthly_goal_achieved else ' 🔴 Failed'}**
Target: {MONTHLY_ORG_GOAL} successful contributions
{chr(10).join(f"- {org}: 🟢 {stats['success']} merged | 🔴 {stats['failed']} closed" for org, stats in monthly_org_stats.items())}
**Total: {total_monthly_success}/{MONTHLY_ORG_GOAL}**

</td>
<td width="33%" align="center">

### 🔄 Weekly Pull Requests
**Goal Status: {' 🟢 Achieved' if weekly_goal_achieved else ' 🔴 Failed'}**
Target: {WEEKLY_PR_GOAL} pull requests per week
- 🟢 {weekly_success} successfully merged
- 🔴 {weekly_failed} closed without merging
**Total: {weekly_success + weekly_failed}/{WEEKLY_PR_GOAL}**

</td>
</tr>
</table>

</div>

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