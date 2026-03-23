# Creates a CSV with contributor retention rates for list of GitHub urls
# A contributor is considered "retained" if the time between their first commit and most recent commit is at least `WINDOW_SIZE` number of days apart.
# In theory, a repo with healthy growth should have a higher retention rate,
#   but it's not a perfect metric as a project that accepts small one-off commits from random devs will have a lower retention rate.


#### Variables ####
from repos import REPOS
WINDOW_SIZE = 14 # Minimum number of days apart from first to most recent commit to be considered retained
WINDOW_BUFFER = 15 # Don't count users who's first commit wasn't at least this many days ago

#### Imports ####
import os
import subprocess
import csv
import time
from datetime import datetime
date_format = "%Y-%m-%d"
from dataclasses import dataclass

#### Data Structs ####
@dataclass
class Contributor:
    first_commit: datetime
    last_commit: datetime

    @property
    def days_active(self):
        return (self.last_commit - self.first_commit).days
    
    @property
    def is_retained(self):
        days_since_first = (datetime.now() - self.first_commit).days
        if days_since_first < WINDOW_BUFFER:
            return "Contributor's first commit was too recent to mark as retained or not"
        return self.days_active > WINDOW_SIZE

@dataclass
class Commit:
    date: datetime
    user_id: str

@dataclass
class RepoStats:
    retained: int
    not_retained: int
    too_recent: int
    repo_url: str

    @property
    def retention_rate(self):
        eligible = self.retained + self.not_retained
        return self.retained / eligible if eligible > 0 else 0.0

#### Methods ####
# Clones each repo and then calculates the repo stats
def main():
    if not validate_repo_urls(REPOS):
        raise Exception("Invalid url set in `REPOS`")
    
    results = []
    for repo_link in REPOS:
        print (repo_link)
        clone_repo(repo_link)
        commits = get_commits(repo_link)
        contributors = build_contributors_dataset(commits)
        repo_stats = get_contributor_retention_stats(contributors, repo_link)
        results.append(repo_stats)
        print ()
    save_csv(results)

# Validates valid URLs before starting script
def validate_repo_urls(repo_links):
    for repo_link in repo_links:
        if 'https://github.com/' not in repo_link.lower():
            return False
    return True

# Converts the url of a repo to unique name by separating username and reponame with __
def repo_url_to_unique_name(repo_link):
    repo_link = repo_link.lower()
    unique_name = repo_link.split('https://github.com/')[1].replace('/', '__')
    return unique_name

# Clones repo to unique name
def clone_repo(repo_link):
    unique_name = repo_url_to_unique_name(repo_link)
    os.system(f"git clone {repo_link} {unique_name}")

# Returns a list of `Commit`
# The data is curated by running a `git log` inside the repo's root dir
def get_commits(repo_link):
    unique_name = repo_url_to_unique_name(repo_link)
    if os.path.isdir(unique_name):
        os.chdir(unique_name)
        result = subprocess.run(
            # ["git", "log", "--pretty=format:%ad|%ae", "--date=short"], # Use email as id
            ["git", "log", "--pretty=format:%ad|%an", "--date=short"], # Use name as id
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        os.chdir('../')
        commits = []
        for line in result.stdout.strip().split('\n'):
            date_str, user_id = line.split('|', 1)
            commits.append(Commit(
                date=datetime.strptime(date_str, "%Y-%m-%d"),
                user_id=user_id
            ))
        return commits
    else:
        raise Exception(f"Directory does not exist: {unique_name}")

'''
# I used this to compare the number of unique contributors of using the user_id of name vs email
def count_unique_id(commits):
    uncased_ids = set()
    cased_ids = set()
    
    for commit in commits:
        id = commit[1]
        uncased_ids.add(id.lower())
        cased_ids.add(id)
    
    print (f'unique ids uncased: {len(uncased_ids)}')
    print (f'unique ids cased: {len(cased_ids)}')
'''

# creates a dict of `Contributor` from list of `Commit`
def build_contributors_dataset(commits):
    contributors = {}
    for commit in commits:
        id = commit.user_id.lower()

        if id not in contributors:
            contributors[id] = Contributor(commit.date, commit.date)

        contributors[id].first_commit = min(commit.date, contributors[id].first_commit)
        contributors[id].last_commit = max(commit.date, contributors[id].last_commit)
    
    return contributors

# Calculates the `RepoStats`
def get_contributor_retention_stats(contributors, repo_url):
    retained = 0
    not_retained = 0
    too_recent = 0

    for id in contributors:
        was_retained = contributors[id].is_retained
        if was_retained == True:
            retained += 1
        elif was_retained == False:
            not_retained += 1
        else:
            too_recent += 1

    return RepoStats(retained, not_retained, too_recent, repo_url)

# Saves list of `RepoStats` to .csv
def save_csv(results):
    with open('github_retention_stats.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['repo_url', f'contributor_retention_rate_atleast{WINDOW_SIZE}days', f'contributors_retained_atleast{WINDOW_SIZE}days', 'contributors_not_retained', 'contributors_too_recent'])
        for r in results:
            writer.writerow([r.repo_url, f"{r.retention_rate:.4f}", r.retained, r.not_retained, r.too_recent])

main()
