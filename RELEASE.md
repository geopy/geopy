# Release process

## Prepare

1. Ensure that all issues in the target milestone are
   closed: https://github.com/geopy/geopy/milestones
1. Add missing `.. versionadded`/`.. versionchanged` directives
   where appropriate.
1. `make authors`, review the changes, `git commit -m "Pull up AUTHORS"`
1. Write changelog in docs.
1. Push the changes, ensure that the CI build is green and all tests pass.

## Release

1. Change version in `geopy/util.py`, commit and push.
1. `make release`. When prompted add the same changelog to the git tag,
   but in markdown instead of rst.
1. Create a new release for the pushed tag at https://github.com/geopy/geopy/releases
1. Upload a GPG signature of the tarball to the just created GitHub release,
   see https://wiki.debian.org/Creating%20signed%20GitHub%20releases
1. Close the milestone, add a new one.

## Check

1. Ensure that the uploaded version works in a clean environment
   (e.g. `docker run -it --rm python:3.7 bash`)
   and execute the examples in README.
1. Ensure that RTD builds have passed and the `stable` version has updated:
   https://readthedocs.org/projects/geopy/builds/
1. Ensure that the CI build for the tag is green.

