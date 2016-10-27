Functional Testing
==================
The directory structure, files, and tests found in this directory all work
together to provide:

* a set of machines (or even a single one) so that ceph-ansible can run against
* a "scenario" configuration file in Python, that defines what nodes are
  configured to what roles and what 'components' they will test
* tests (in functional/tests/) that will all run unless skipped explicitly when
  testing a distinct feature dependant on the ansible run.


Example run
-----------
The following is the easiest way to try this out locally. Both Vagrant and
VirtualBox are required. Ensure that ``py.test`` and ``pytest-xdist`` are
installed (with pip on a virtualenv) by using the ``requirements.txt`` file in
the ``tests`` directory::

    pip install -r requirements.txt

Choose a directory in ``tests/functional`` that has 3 files:

* ``Vagrantfile``
* ``vagrant_variables.yml``
* A Python ("scenario") file.

For example in: ``tests/functional/ubuntu/16.04/mon/initial_members``::

    tree .
    .
    ├── Vagrantfile -> ../../../../../../Vagrantfile
    ├── scenario.py
    └── vagrant_variables.yml

    0 directories, 3 files

It is *required* to be in that directory. It is what triggers all the
preprocessing of complex arguments based on the cluster setup.

Run vagrant first to setup the environment::

   vagrant up --no-provision --provider=virtualbox

Then run ceph-ansible against the hosts with the distinct role (in this case we
are deploying a monitor using ``initial_members``).

And finally run ``py.test``::

    py.test -v
