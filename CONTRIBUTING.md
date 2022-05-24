# Contributing to ceph-ansible

1. Follow the [commit guidelines](#commit-guidelines)

## Commit guidelines

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

[Suggested reading.](https://chris.beams.io/posts/git-commit/)

## Pull requests

### Jenkins CI

We use Jenkins to run several tests on each pull request.

If you don't want to run a build for a particular pull request, because all you are changing is the
README for example, add the text `[skip ci]` to the PR title.

### Merging strategy

Merging PR is controlled by [mergify](https://mergify.io/) by the following rules:

- at least one approuval from a maintainer
- a SUCCESS from the CI pipeline "ceph-ansible PR Pipeline"

If you work is not ready for review/merge, please request the DNM label via a comment or the title of your PR.
This will prevent the engine merging your pull request.

### Backports (maintainers only)

If you wish to see your work from 'main' being backported to a stable branch you can ping a maintainer
so he will set the backport label on your PR. Once the PR from main is merged, a backport PR will be created by mergify,
if there is a cherry-pick conflict you must resolv it by pulling the branch.

**NEVER** push directly into a stable branch, **unless** the code from main has diverged so much that the files don't exist in the stable branch.
If that happens, inform the maintainers of the reasons why you pushed directly into a stable branch, if the reason is invalid, maintainers will immediatly close your pull request.

## Good to know

### Sample files

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
- `./roles/ceph-container-common/defaults/main.yml`
- `./roles/ceph-common-coreos/defaults/main.yml`

You will have to get the corresponding sample file updated, there is a script which do it for you.
You must run `./generate_group_vars_sample.sh` before you commit your changes so you are guaranteed to have consistent content for these files.

### Keep your branch up-to-date

Sometimes, a pull request can be subject to long discussion, reviews and comments, meantime, `main`
moves forward so let's try to keep your branch rebased on main regularly to avoid huge conflict merge.
A rebased branch is more likely to be merged easily & shorter.

### Organize your commits

Do not split your commits unecessary, we are used to see pull request with useless additional commits like
"I'm addressing reviewer's comments". So, please, squash and/or amend them as much as possible.

Similarly, split them when needed, if you are modifying several parts in ceph-ansible or pushing a large
patch you may have to split yours commit properly so it's better to understand your work.
Some recommandations:

- one fix = one commit,
- do not mix multiple topics in a single commit,
- if you PR contains a large number of commits that are each other totally unrelated, it should probably even be split in several PRs.

If you've broken your work up into a set of sequential changes and each commit pass the tests on their own then that's fine.
If you've got commits fixing typos or other problems introduced by previous commits in the same PR, then those should be squashed before merging.

If you are new to Git, these links might help:

- [https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History)
- [http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html](http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html)
