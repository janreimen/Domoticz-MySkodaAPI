Yes. Once development has been tested and you want to bring it into master, I recommend doing the merge on rpi4dmz, where master is your production branch.

1. On rpi4prod — make sure master is clean
cd /srv/domoticz/plugins/Domoticz-MySkodaAPI

git status
git switch master
git pull origin master

Make sure git status doesn't show uncommitted changes.

2. Fetch the latest development branch
git fetch origin
3. Merge development into master
git merge origin/development

If there are no conflicts, Git will create the merge commit.

4. Push master to GitHub
git push origin master

Now:

GitHub
   │
   ├── master       ← production / rpi4dmz
   │
   └── development  ← testing / rpi4office
                         │
                         └── tested
                              ↓
                         merge into master
If you want a very clean workflow

After testing:

# rpi4dmz
git switch master
git pull origin master
git fetch origin
git merge origin/development
git push origin master

Then rpi4prod remains on master, while rpi4office remains on development.

One important point for your MySkodaAPI project: don't delete development after 
merging if you intend to keep using rpi4development as the permanent testing environment. 
It can continue diverging from master for the next development cycle.
