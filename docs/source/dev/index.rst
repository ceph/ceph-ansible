Contribution Guidelines
=======================

The repository centralises all the Ansible roles. The roles are all part of the Ansible Galaxy.

We love contribution and we love giving visibility to our contributors, this is why all the **commits must be signed-off**.

Mailing list
------------

Please register the mailing list at http://lists.ceph.com/listinfo.cgi/ceph-ansible-ceph.com.

IRC
---

Feel free to join us in the channel ``#ceph-ansible`` of the OFTC servers (https://www.oftc.net).

GitHub
------

The main GitHub account for the project is at https://github.com/ceph/ceph-ansible/.

Submit a patch
--------------

To start contributing just do:

.. code-block:: console

   $ git checkout -b my-working-branch
   $ # do your changes #
   $ git add -p

If your change impacts a variable file in a role such as ``roles/ceph-common/defaults/main.yml``, you need to generate a ``group_vars`` file:

.. code-block:: console

   $ ./generate_group_vars_sample.sh

You are finally ready to push your changes on GitHub:

.. code-block:: console

   $ git commit -s
   $ git push origin my-working-branch

Worked on a change and you don't want to resend a commit for a syntax fix?

.. code-block:: console

   $ # do your syntax change #
   $ git commit --amend
   $ git push -f origin my-working-branch

Pull Request Testing
--------------------

Pull request testing is handled by Jenkins. All test must pass before your pull request will be merged.

All of tests that are running are listed in the GitHub UI and will list their current status.

If a test fails and you'd like to rerun it, comment on your pull request in the following format:

.. code-block:: none

   jenkins test $scenario_name

For example:

.. code-block:: none

   jenkins test centos-non_container-all_daemons

Backporting changes
-------------------

If a change should be backported to a ``stable-*`` Git branch:

- Mark your pull request with the GitHub label "Backport" so we don't lose track of it.
- Fetch the latest updates into your clone: ``git fetch``
- Determine the latest available stable branch:
  ``git branch -r --list "origin/stable-[0-9].[0-9]" | sort -r | sed 1q``
- Create a new local branch for your pull request, based on the stable branch:
  ``git checkout --no-track -b my-backported-change origin/stable-5.0``
- Cherry-pick your change: ``git cherry-pick -x (your-sha1)``
- Create a new pull request against the ``stable-5.0`` branch.
- Ensure that your pull request's title has the prefix "backport:", so it's clear
  to reviewers what this is about.
- Add a comment in your backport pull request linking to the original (main) pull request.

All changes to the stable branches should land in main first, so we avoid
regressions.

Once this is done, one of the project maintainers will tag the tip of the
stable branch with your change. For example:

.. code-block:: console

   $ git checkout stable-5.0
   $ git pull --ff-only
   $ git tag v5.0.12
   $ git push origin v5.0.12
