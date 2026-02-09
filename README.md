# Cloning the Repo (only needs to be done once)

```git clone https://github.com/LW95x/bus-project.git```

# Sample Workflow

Pull the most recent version of the repository
```git pull origin main```

Create a branch
```git checkout -b <branch-name>```

Add, commit, push branch
```
git add .
git commit -m "detailed commit message"
git push -u origin <branch-name>
```

Open Pull Request (PR) on GitHub

After PR is merged
```
git checkout main
git pull origin main
git branch -d <branch-name>
```
