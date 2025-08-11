#! /bin/bash

ORIGIN=$(git remote get-url origin)
REPO=$(basename $ORIGIN .git)

cd ..

# update or create mirror
if [ -d $REPO.git ]; then
    cd $REPO.git
    git remote update
else
    git clone --mirror $ORIGIN
    cd $REPO.git
fi

git bundle create ../$REPO.bundle --all
printf "Created bundle at ../$REPO.bundle\n\n"

# If Git LFS is enabled
git lfs fetch --all
tar -czf ../$REPO-lfs.tar lfs
echo Created lfs tar at ../$REPO-lfs.tar

cd ../$REPO