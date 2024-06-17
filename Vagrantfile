# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'
require 'resolv'
VAGRANTFILE_API_VERSION = '2'

if File.file?(File.join(File.dirname(__FILE__), 'vagrant_variables.yml')) then
  vagrant_variables_file = 'vagrant_variables.yml'
else
  vagrant_variables_file = 'vagrant_variables.yml.sample'
end

config_file=File.expand_path(File.join(File.dirname(__FILE__), vagrant_variables_file))

settings=YAML.load_file(config_file)

LABEL_PREFIX    = settings['label_prefix'] ? settings['label_prefix'] + "-" : ""
NMONS           = settings['mon_vms']
NOSDS           = settings['osd_vms']
NMDSS           = settings['mds_vms']
NRGWS           = settings['rgw_vms']
NNFSS           = settings['nfs_vms']
NRBD_MIRRORS    = settings['rbd_mirror_vms']
CLIENTS         = settings['client_vms']
MGRS            = settings['mgr_vms']
PUBLIC_SUBNET   = settings['public_subnet']
CLUSTER_SUBNET  = settings['cluster_subnet']
BOX             = ENV['CEPH_ANSIBLE_VAGRANT_BOX'] || settings['vagrant_box']
CLIENT_BOX      = ENV['CEPH_ANSIBLE_VAGRANT_BOX'] || settings['client_vagrant_box'] || BOX
BOX_URL         = ENV['CEPH_ANSIBLE_VAGRANT_BOX_URL'] || settings['vagrant_box_url']
SYNC_DIR        = settings['vagrant_sync_dir']
MEMORY          = settings['memory']
ETH             = settings['eth']
DOCKER          = settings['docker']
USER            = settings['ssh_username']
DEBUG           = settings['debug']

ASSIGN_STATIC_IP = !(BOX == 'openstack' or BOX == 'linode')
DISABLE_SYNCED_FOLDER = settings.fetch('vagrant_disable_synced_folder', false)

"#{PUBLIC_SUBNET}" =~ Resolv::IPv6::Regex ? IPV6 = true : IPV6 = false

$last_ip_pub_digit   = 9
$last_ip_cluster_digit = 9

ansible_provision = proc do |ansible|
  if DOCKER then
    ansible.playbook = 'site-container.yml'
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
    'mgrs'             => (0..MGRS - 1).map { |j| "#{LABEL_PREFIX}mgr#{j}" },
  }

  if IPV6 then
    ansible.extra_vars = {
        cluster_network: "#{CLUSTER_SUBNET}/64",
        journal_size: 100,
        public_network: "#{PUBLIC_SUBNET}/64",
    }
  else
    ansible.extra_vars = {
        cluster_network: "#{CLUSTER_SUBNET}.0/24",
        journal_size: 100,
        public_network: "#{PUBLIC_SUBNET}.0/24",
    }
  end

  # In a production deployment, these should be secret
  if DOCKER then
    ansible.extra_vars = ansible.extra_vars.merge({
      containerized_deployment: 'true',
      ceph_mon_docker_subnet: ansible.extra_vars[:public_network],
      devices: settings['disks'],
      radosgw_interface: ETH,
      generate_fsid: 'true',
    })
  else
    ansible.extra_vars = ansible.extra_vars.merge({
      devices: settings['disks'],
      radosgw_interface: ETH,
      os_tuning_params: settings['os_tuning_params'],
    })
  end

  if BOX == 'linode' then
    ansible.sudo = true
    # Use radosgw_address_block instead of radosgw_interface:
    ansible.extra_vars.delete(:radosgw_interface)
    ansible.extra_vars = ansible.extra_vars.merge({
      cluster_network: "#{CLUSTER_SUBNET}.0/16",
      devices: ['/dev/sdc'], # hardcode leftover disk
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
    lv.disk_driver :cache => 'unsafe'
    lv.graphics_type = 'none'
    lv.cpus = 2
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

      if settings['os_networks'] then
        os.networks = settings['os_networks']
      end

      if settings['os_floating_ip_pool'] then
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

  (0..NMONS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}mon#{i}" do |mon|
      mon.vm.hostname = "#{LABEL_PREFIX}mon#{i}"
      if ASSIGN_STATIC_IP && !IPV6
	  mon.vm.network :private_network,
	  :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
      end

      # Virtualbox
      mon.vm.provider :virtualbox do |vb,override|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end

      # VMware
      mon.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Libvirt
      mon.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end  
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

  (0..MGRS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}mgr#{i}" do |mgr|
      mgr.vm.hostname = "#{LABEL_PREFIX}mgr#{i}"
      if ASSIGN_STATIC_IP && !IPV6
	  mgr.vm.network :private_network,
	  :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      mgr.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end
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
      if ASSIGN_STATIC_IP && !IPV6
	  client.vm.network :private_network,
	  :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      client.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end
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
      if ASSIGN_STATIC_IP && !IPV6
	  rgw.vm.network :private_network,
	  :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      rgw.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end
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
      if ASSIGN_STATIC_IP && !IPV6
          nfs.vm.network :private_network,
	  :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      nfs.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end
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
      if ASSIGN_STATIC_IP && !IPV6
	  mds.vm.network :private_network,
          :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      mds.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end  
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
      if ASSIGN_STATIC_IP && !IPV6
	  rbd_mirror.vm.network :private_network,
          :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
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
      rbd_mirror.vm.provider :libvirt do |lv,override|
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	  :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	  :libvirt__ipv6_prefix => "64",
	  :libvirt__dhcp_enabled => false,
	  :libvirt__forward_mode => "veryisolated",
	  :libvirt__network_name => "ipv6-public-network",
	  :ip => "#{PUBLIC_SUBNET}#{$last_ip_pub_digit+=1}",
	  :netmask => "64"
	end
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

  (0..NOSDS - 1).each do |i|
    config.vm.define "#{LABEL_PREFIX}osd#{i}" do |osd|
      osd.vm.hostname = "#{LABEL_PREFIX}osd#{i}"
      if ASSIGN_STATIC_IP && !IPV6
	  osd.vm.network :private_network,
          :ip => "#{PUBLIC_SUBNET}.#{$last_ip_pub_digit+=1}"
	  osd.vm.network :private_network,
          :ip => "#{CLUSTER_SUBNET}.#{$last_ip_cluster_digit+=1}"
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

        (0..2).each do |d|
          unless File.exist?("disk-#{i}-#{d}.vdi")
          vb.customize ['createhd',
                        '--filename', "disk-#{i}-#{d}",
                        '--size', '11000']
          end
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
      osd.vm.provider :libvirt do |lv,override|
        # always make /dev/sd{a/b/c} so that CI can ensure that
        # virtualbox and libvirt will have the same devices to use for OSDs
        (0..2).each do |d|
          lv.storage :file, :device => "hd#{driverletters[d]}", :size => '50G', :bus => "ide"
        end
        lv.memory = MEMORY
        lv.random_hostname = true
	if IPV6 then
	  override.vm.network :private_network,
	    :libvirt__ipv6_address => "#{PUBLIC_SUBNET}",
	    :libvirt__ipv6_prefix => "64",
	    :libvirt__dhcp_enabled => false,
	    :libvirt__forward_mode => "veryisolated",
	    :libvirt__network_name => "ipv6-public-network",
	    :netmask => "64"
	  override.vm.network :private_network,
	    :libvirt__ipv6_address => "#{CLUSTER_SUBNET}",
	    :libvirt__ipv6_prefix => "64",
	    :libvirt__dhcp_enabled => false,
	    :libvirt__forward_mode => "veryisolated",
	    :libvirt__network_name => "ipv6-cluster-network",
	    :netmask => "64"
	end
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
