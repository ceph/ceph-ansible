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

Good to know
------------

#### Sample files
The sample files we provide in `group_vars/` are versionned,
they are a copy of what their respective `./roles/<role>/defaults/main.yml` contain.

It means if you are pushing a patch modifying one of these files:

- `./roles/ceph-mds/defaults/main.yml`
- `./roles/ceph-mgr/defaults/main.yml`
- `./roles/ceph-fetch-keys/defaults/main.yml`
- `./roles/ceph-rbd-mirror/defaults/main.yml`
- `./roles/ceph-defaults/defaults/main.yml`
- `./roles/ceph-osd/defaults/main.yml`
- `./roles/ceph-nfs/defaults/main.yml`
- `./roles/ceph-client/defaults/main.yml`
- `./roles/ceph-common/defaults/main.yml`
- `./roles/ceph-iscsi-gw/defaults/main.yml`
- `./roles/ceph-mon/defaults/main.yml`
- `./roles/ceph-rgw/defaults/main.yml`
- `./roles/ceph-restapi/defaults/main.yml`
- `./roles/ceph-docker-common/defaults/main.yml`
- `./roles/ceph-common-coreos/defaults/main.yml`

You will have to get the corresponding sample file updated, there is a script which do it for you.
You must run `./generate_group_vars_sample.sh` before you commit your changes so you are guaranteed to have consistent content for these files.


#### Keep your branch up-to-date
Sometimes, a pull request can be subject to long discussion, reviews and comments, meantime, `master`
moves forward so let's try to keep your branch rebased on master regularly to avoid huge conflict merge.
A rebased branch is more likely to be merged easily & shorter.


#### Organize your commits
Do not split your commits unecessary, we are used to see pull request with useless additional commits like
"I'm addressing reviewer's comments". So, please, squash and/or amend them as much as possible.

Similarly, split them when needed, if you are modifying several parts in ceph-ansible or pushing a large
patch you may have to split yours commit properly so it's better to understand your work.
Some recommandations:
 - 1 fix = 1 commit,
 - do not mix multiple topics in a single commit,
 - if you PR contains a large number of commits that are each other totally unrelated, it should probably even be split in several PRs.
