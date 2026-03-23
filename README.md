# GitHub Contributor Retention
This repo generates stats of the contributor retention rate for a list of GitHub repos.  
A contributor is considered "retained" if they have 2 commits at least 30 days apart.  

# Usage
## Step 1: Repo Selection
Update the variable `REPOS` in `repos.py`.  

## Step 2: Clone Repos and Report Stats
```$python clone_repos.py```  

## Step 3: View Results
Stats are exported to `github_retention_stats.csv`  
