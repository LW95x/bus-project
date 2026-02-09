# Cloning the Repo (only needs to be done once)

```git clone https://github.com/LW95x/bus-project.git```

# Sample Workflow

1. Pull the most recent version of the repository
```git pull origin main```

2. Create a branch
```git checkout -b <branch-name>```

3. Add, commit, push branch
```
git add .
git commit -m "detailed commit message"
git push -u origin <branch-name>
```

4. Open Pull Request (PR) on GitHub

5. After PR is merged
```
git checkout main
git pull origin main
git branch -d <branch-name>
```
