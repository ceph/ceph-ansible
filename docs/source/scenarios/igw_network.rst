**************************************************************************************
Deploying the dashboard with iSCSI node in a different subnet than ``public_network``
**************************************************************************************

If the ceph ``public network`` is ``2a00:8a60:1:c301::/64`` and the iSCSI Gateway is in a dedicated gateway network ``2a00:8a60:1:c300::/64``

You have to set the ``igw_network`` variable with the subnet of your iSCSI gateway.

.. code-block:: yaml

    igw_network: "2a00:8a60:1:c300::/64"

default value is ``{{ public_network }}``