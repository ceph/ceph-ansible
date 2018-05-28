Contributing to ceph-ansible
==============================

1. Follow the [commit guidelines](#commit-guidelines)


Commit guidelines
-----------------
- All commits should have a subject and a body
- The commit subject should briefly describe what the commit changes
- The commit body should describe the problem addressed and the chosen solution
  - What was the problem and solution? Why that solution? Were there alternative ideas?
- Wrap commit subjects and bodies to 80 characters
- Sign-off your commits
- Add a best-effort scope designation to commit subjects. This could be a directory name, file name,
  or the name of a logical grouping of code. Examples:
  - library: add a placeholder module for the validate action plugin
  - site.yml: combine validate play with fact gathering play
  - rhcs: bump version to 3.0 for stable 3.1
- Commits linked with an issue should trace them with :
  - Fixes: #2653

Suggested reading: https://chris.beams.io/posts/git-commit/


CI
-----

### Jenkins
We use Jenkins to run several tests on each pull request.

If you don't want to run a build for a particular pull request, because all you are changing is the
README for example, add the text `[skip ci]` to the PR title.
