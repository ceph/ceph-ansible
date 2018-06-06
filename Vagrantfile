# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'
require 'time'
VAGRANTFILE_API_VERSION = '2'

config_file=File.expand_path(File.join(File.dirname(__FILE__), 'vagrant_variables.yml'))
settings=YAML.load_file(config_file)

LABEL_PREFIX    = settings['label_prefix'] ? settings['label_prefix'] + "-" : ""
NMONS           = settings['mon_vms']
NOSDS           = settings['osd_vms']
NMDSS           = settings['mds_vms']
NRGWS           = settings['rgw_vms']
NNFSS           = settings['nfs_vms']
RESTAPI         = settings['restapi']
NRBD_MIRRORS    = settings['rbd_mirror_vms']
CLIENTS         = settings['client_vms']
NISCSI_GWS      = settings['iscsi_gw_vms']
MGRS            = settings['mgr_vms']
PUBLIC_SUBNET   = settings['public_subnet']
CLUSTER_SUBNET  = settings['cluster_subnet']
BOX             = settings['vagrant_box']
CLIENT_BOX      = settings['client_vagrant_box'] || settings['vagrant_box']
BOX_URL         = settings['vagrant_box_url']
SYNC_DIR        = settings['vagrant_sync_dir']
MEMORY          = settings['memory']
ETH             = settings['eth']
DOCKER          = settings['docker']
USER            = settings['ssh_username']
DEBUG           = settings['debug']

ASSIGN_STATIC_IP = !(BOX == 'openstack' or BOX == 'linode')
DISABLE_SYNCED_FOLDER = settings.fetch('vagrant_disable_synced_folder', false)
DISK_UUID = Time.now.utc.to_i


ansible_provision = proc do |ansible|
  if DOCKER then
    ansible.playbook = 'site-docker.yml'
    if settings['skip_tags']
      ansible.skip_tags = settings['skip_tags']
    end
  else
    ansible.playbook = 'site.yml'
  end

  # Note: Can't do ranges like mon[0-2] in groups because
  # these aren't supported by Vagrant, see
  # https://github.com/mitchellh/vagrant/issues/3539
  ansible.groups = {
    'mons'             => (0..NMONS - 1).map { |j| "#{LABEL_PREFIX}mon#{j}" },
    'osds'             => (0..NOSDS - 1).map { |j| "#{LABEL_PREFIX}osd#{j}" },
    'mdss'             => (0..NMDSS - 1).map { |j| "#{LABEL_PREFIX}mds#{j}" },
    'rgws'             => (0..NRGWS - 1).map { |j| "#{LABEL_PREFIX}rgw#{j}" },
    'nfss'             => (0..NNFSS - 1).map { |j| "#{LABEL_PREFIX}nfs#{j}" },
    'rbd_mirrors'      => (0..NRBD_MIRRORS - 1).map { |j| "#{LABEL_PREFIX}rbd_mirror#{j}" },
    'clients'          => (0..CLIENTS - 1).map { |j| "#{LABEL_PREFIX}client#{j}" },
    'iscsigws'        => (0..NISCSI_GWS - 1).map { |j| "#{LABEL_PREFIX}iscsi_gw#{j}" },
    'mgrs'             => (0..MGRS - 1).map { |j| "#{LABEL_PREFIX}mgr#{j}" }
  }

  if RESTAPI then
    ansible.groups['restapis'] = (0..NMONS - 1).map { |j| "#{LABEL_PREFIX}mon#{j}" }
  end

  ansible.extra_vars = {
      cluster_network: "#{CLUSTER_SUBNET}.0/24",
      journal_size: 100,
      public_network: "#{PUBLIC_SUBNET}.0/24",
  }

  # In a production deployment, these should be secret
  if DOCKER then
    ansible.extra_vars = ansible.extra_vars.merge({
      containerized_deployment: 'true',
      monitor_interface: ETH,
      ceph_mon_docker_subnet: "#{PUBLIC_SUBNET}.0/24",
      devices: settings['disks'],
      ceph_docker_on_openstack: BOX == 'openstack',
      radosgw_interface: ETH,
      generate_fsid: 'true',
    })
  else
    ansible.extra_vars = ansible.extra_vars.merge({
      devices: settings['disks'],
      osd_scenario: 'collocated',
      monitor_interface: ETH,
      radosgw_interface: ETH,
      os_tuning_params: settings['os_tuning_params'],
      pool_default_size: '2',
    })
  end

  if BOX == 'linode' then
    ansible.sudo = true
    # Use monitor_address_block instead of monitor_interface:
    ansible.extra_vars.delete(:monitor_interface)
    # Use radosgw_address_block instead of radosgw_interface:
    ansible.extra_vars.delete(:radosgw_interface)
    ansible.extra_vars = ansible.extra_vars.merge({
      cluster_network: "#{CLUSTER_SUBNET}.0/16",
      devices: ['/dev/sdc'], # hardcode leftover disk
      osd_scenario: 'collocated',
      monitor_address_block: "#{PUBLIC_SUBNET}.0/16",
      radosgw_address_block: "#{PUBLIC_SUBNET}.0/16",
      public_network: "#{PUBLIC_SUBNET}.0/16",
    })
  end

  if DEBUG then
    ansible.verbose = '-vvvv'
  end
  ansible.limit = 'all'
end

def create_vmdk(name, size)
  dir = Pathname.new(__FILE__).expand_path.dirname
  path = File.join(dir, '.vagrant', name + '.vmdk')
  `vmware-vdiskmanager -c -s #{size} -t 0 -a scsi #{path} \
   2>&1 > /dev/null` unless File.exist?(path)
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = BOX
  config.vm.box_url = BOX_URL
  config.ssh.insert_key = false # workaround for https://github.com/mitchellh/vagrant/issues/5048
  config.ssh.private_key_path = settings['ssh_private_key_path']
  config.ssh.username = USER

  # When using libvirt, avoid errors like:
  # "host doesn't support requested feature: CPUID.01H:EDX.ds [bit 21]"
  config.vm.provider :libvirt do |lv|
    lv.cpu_mode = 'host-passthrough'
    lv.volume_cache = 'unsafe'
    lv.graphics_type = 'none'
  end

  # Faster bootup. Disables mounting the sync folder for libvirt and virtualbox
  if DISABLE_SYNCED_FOLDER
    config.vm.provider :virtualbox do |v,override|
      override.vm.synced_folder '.', SYNC_DIR, disabled: true
    end
    config.vm.provider :libvirt do |v,override|
      override.vm.synced_folder '.', SYNC_DIR, disabled: true
    end
  end

  if BOX == 'openstack'
    # OpenStack VMs
    config.vm.provider :openstack do |os|
      config.vm.synced_folder ".", "/home/#{USER}/vagrant", disabled: true
      config.ssh.pty = true
      os.openstack_auth_url = settings['os_openstack_auth_url']
      os.username = settings['os_username']
      os.password = settings['os_password']
      os.tenant_name = settings['os_tenant_name']
      os.region = settings['os_region']
      os.flavor = settings['os_flavor']
      os.image = settings['os_image']
      os.keypair_name = settings['os_keypair_name']
      os.security_groups = ['default']

      if settings['os.networks'] then
        os.networks = settings['os_networks']
      end

      if settings['os.floating_ip_pool'] then
        os.floating_ip_pool = settings['os_floating_ip_pool']
      end

      config.vm.provision "shell", inline: "true", upload_path: "/home/#{USER}/vagrant-shell"
    end
  elsif BOX == 'linode'
    config.vm.provider :linode do |provider, override|
      provider.token = ENV['LINODE_API_KEY']
      provider.distribution = settings['cloud_distribution'] # 'Ubuntu 16.04 LTS'
      provider.datacenter = settings['cloud_datacenter']
      provider.plan = MEMORY.to_s
      provider.private_networking = true
      # root install generally takes <1GB
      provider.xvda_size = 4*1024
      # add some swap as the Linode distros require it
      provider.swap_size = 128
    end
  end

  (0..MGRS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}mgr#{i}" do |mgr|
      mgr.vm.hostname = "#{LABEL_PREFIX}mgr#{i}"
      if ASSIGN_STATIC_IP
        mgr.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.3#{i}"
      end
      # Virtualbox
      mgr.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      mgr.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      mgr.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      mgr.vm.provider "parallels" do |prl|
        prl.name = "ceph-mgr#{i}"
        prl.memory = "#{MEMORY}"
      end

      mgr.vm.provider :linode do |provider|
        provider.label = mgr.vm.hostname
      end
    end
  end

  (0..CLIENTS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}client#{i}" do |client|
      client.vm.box = CLIENT_BOX
      client.vm.hostname = "#{LABEL_PREFIX}client#{i}"
      if ASSIGN_STATIC_IP
        client.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.4#{i}"
      end
      # Virtualbox
      client.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      client.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      client.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      client.vm.provider "parallels" do |prl|
        prl.name = "ceph-client#{i}"
        prl.memory = "#{MEMORY}"
      end

      client.vm.provider :linode do |provider|
        provider.label = client.vm.hostname
      end
    end
  end

  (0..NRGWS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}rgw#{i}" do |rgw|
      rgw.vm.hostname = "#{LABEL_PREFIX}rgw#{i}"
      if ASSIGN_STATIC_IP
        rgw.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.5#{i}"
      end

      # Virtualbox
      rgw.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      rgw.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      rgw.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      rgw.vm.provider "parallels" do |prl|
        prl.name = "ceph-rgw#{i}"
        prl.memory = "#{MEMORY}"
      end

      rgw.vm.provider :linode do |provider|
        provider.label = rgw.vm.hostname
      end
    end
  end

  (0..NNFSS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}nfs#{i}" do |nfs|
      nfs.vm.hostname = "#{LABEL_PREFIX}nfs#{i}"
      if ASSIGN_STATIC_IP
        nfs.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.6#{i}"
      end

      # Virtualbox
      nfs.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      nfs.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      nfs.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      nfs.vm.provider "parallels" do |prl|
        prl.name = "ceph-nfs#{i}"
        prl.memory = "#{MEMORY}"
      end

      nfs.vm.provider :linode do |provider|
        provider.label = nfs.vm.hostname
      end
    end
  end

  (0..NMDSS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}mds#{i}" do |mds|
      mds.vm.hostname = "#{LABEL_PREFIX}mds#{i}"
      if ASSIGN_STATIC_IP
        mds.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.7#{i}"
      end
      # Virtualbox
      mds.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      mds.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      mds.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end
      # Parallels
      mds.vm.provider "parallels" do |prl|
        prl.name = "ceph-mds#{i}"
        prl.memory = "#{MEMORY}"
      end

      mds.vm.provider :linode do |provider|
        provider.label = mds.vm.hostname
      end
    end
  end

  (0..NRBD_MIRRORS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}rbd-mirror#{i}" do |rbd_mirror|
      rbd_mirror.vm.hostname = "#{LABEL_PREFIX}rbd-mirror#{i}"
      if ASSIGN_STATIC_IP
        rbd_mirror.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.8#{i}"
      end
      # Virtualbox
      rbd_mirror.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      rbd_mirror.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      rbd_mirror.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end
      # Parallels
      rbd_mirror.vm.provider "parallels" do |prl|
        prl.name = "ceph-rbd-mirror#{i}"
        prl.memory = "#{MEMORY}"
      end

      rbd_mirror.vm.provider :linode do |provider|
        provider.label = rbd_mirror.vm.hostname
      end
    end
  end

  (0..NISCSI_GWS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}iscsi-gw#{i}" do |iscsi_gw|
      iscsi_gw.vm.hostname = "#{LABEL_PREFIX}iscsi-gw#{i}"
      if ASSIGN_STATIC_IP
        iscsi_gw.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.9#{i}"
      end
      # Virtualbox
      iscsi_gw.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      iscsi_gw.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      iscsi_gw.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end
      # Parallels
      iscsi_gw.vm.provider "parallels" do |prl|
        prl.name = "iscsi-gw#{i}"
        prl.memory = "#{MEMORY}"
      end

      iscsi_gw.vm.provider :linode do |provider|
        provider.label = iscsi_gw.vm.hostname
      end
    end
  end

  (0..NMONS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}mon#{i}" do |mon|
      mon.vm.hostname = "#{LABEL_PREFIX}mon#{i}"
      if ASSIGN_STATIC_IP
        mon.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.1#{i}"
      end
      # Virtualbox
      mon.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      mon.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      mon.vm.provider :libvirt do |lv|
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      mon.vm.provider "parallels" do |prl|
        prl.name = "ceph-mon#{i}"
        prl.memory = "#{MEMORY}"
      end

      mon.vm.provider :linode do |provider|
        provider.label = mon.vm.hostname
      end
    end
  end

  (0..NOSDS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}osd#{i}" do |osd|
      osd.vm.hostname = "#{LABEL_PREFIX}osd#{i}"
      if ASSIGN_STATIC_IP
        osd.vm.network :private_network,
          ip: "#{PUBLIC_SUBNET}.10#{i}"
        osd.vm.network :private_network,
          ip: "#{CLUSTER_SUBNET}.20#{i}"
      end
      # Virtualbox
      osd.vm.provider :virtualbox do |vb|
        # Create our own controller for consistency and to remove VM dependency
        unless File.exist?("disk-#{i}-0.vdi")
          # Adding OSD Controller;
          # once the first disk is there assuming we don't need to do this
          vb.customize ['storagectl', :id,
                        '--name', 'OSD Controller',
                        '--add', 'scsi']
        end

        (0..1).each do |d|
          vb.customize ['createhd',
                        '--filename', "disk-#{i}-#{d}",
                        '--size', '11000'] unless File.exist?("disk-#{i}-#{d}.vdi")
          vb.customize ['storageattach', :id,
                        '--storagectl', 'OSD Controller',
                        '--port', 3 + d,
                        '--device', 0,
                        '--type', 'hdd',
                        '--medium', "disk-#{i}-#{d}.vdi"]
        end
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      osd.vm.provider :vmware_fusion do |v|
        (0..1).each do |d|
          v.vmx["scsi0:#{d + 1}.present"] = 'TRUE'
          v.vmx["scsi0:#{d + 1}.fileName"] =
            create_vmdk("disk-#{i}-#{d}", '11000MB')
        end
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      driverletters = ('a'..'z').to_a
      osd.vm.provider :libvirt do |lv|
        # always make /dev/sd{a/b/c} so that CI can ensure that
        # virtualbox and libvirt will have the same devices to use for OSDs
        (0..2).each do |d|
          lv.storage :file, :device => "hd#{driverletters[d]}", :path => "disk-#{i}-#{d}-#{DISK_UUID}.disk", :size => '50G', :bus => "ide"
        end
        lv.memory = MEMORY
        lv.random_hostname = true
      end

      # Parallels
      osd.vm.provider "parallels" do |prl|
        prl.name = "ceph-osd#{i}"
        prl.memory = "#{MEMORY}"
        (0..1).each do |d|
          prl.customize ["set", :id,
                         "--device-add",
                         "hdd",
                         "--iface",
                         "sata"]
        end
      end

      osd.vm.provider :linode do |provider|
        provider.label = osd.vm.hostname
      end

      # Run the provisioner after the last machine comes up
      osd.vm.provision 'ansible', &ansible_provision if i == (NOSDS - 1)
    end
  end
end
