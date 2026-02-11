# Cloning the Repo (only needs to be done once)

Create a new directory, ensure the terminal is inside the newly created directory, then paste the following:
```git clone https://github.com/LW95x/bus-project.git```

# Sample Workflow

1. Pull the most recent version of the repository (always do this before you start making changes to the existing codebase)
```
git pull origin main
```

3. Create a branch (this encapsulates the changes to the codebase you are going to make)
```
git checkout -b <branch-name>
```

5. (Submitting your code for review) Add, commit, push branch
```
git add .
git commit -m "detailed commit message"
git push -u origin <branch-name>
```

4. Open Pull Request (PR) on GitHub: after you push your branch, you will see an option to create a PR at the top of the repository (this page) - wait until this has been peer-reviewed before merging with the main codebase

5. After the pull request is merged (repeat from step 1)
```
git checkout main
git pull origin main
git branch -d <branch-name>
```
