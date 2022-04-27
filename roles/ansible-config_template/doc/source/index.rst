======================
Config Template plugin
======================

Synopsis
--------
Renders template files providing a create/update override interface

- The module contains the template functionality with the ability to override
  items in config, in transit, through the use of a simple dictionary without
  having to write out various temp files on target machines. The module renders
  all of the potential jinja a user could provide in both the template file and
  in the override dictionary which is ideal for deployers who may have lots of
  different configs using a similar code base.
- The module is an extension of the **copy** module and all of attributes that
  can be set there are available to be set here.

Loading
-------

To use the plugin, include this role in your meta/main.yml dependencies

.. code-block :: yaml

   dependencies:
     - role: ansible-config_template

Alternatively, move the role to the appropriate plugin folder location
of your ansible configuration.

Example role requirement overload for automatic plugin download
---------------------------------------------------------------

The Ansible role requirement file can be used to overload the
``ansible-galaxy`` command to automatically fetch the plugins for
you in a given project. To do this add the following lines to your
``ansible-role-requirements.yml`` file.

.. literalinclude:: ../../examples/ansible-role-requirements.yml
   :language: yaml

Examples
--------

.. literalinclude:: ../../library/config_template
   :language: yaml
   :start-after: EXAMPLES = """
   :end-before: """
