# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'
VAGRANTFILE_API_VERSION = '2'

config_file=File.expand_path(File.join(File.dirname(__FILE__), 'vagrant_variables.yml'))
settings=YAML.load_file(config_file)

NMONS      = settings['mon_vms']
NOSDS      = settings['osd_vms']
NMDSS      = settings['mds_vms']
NRGWS      = settings['rgw_vms']
NNFSS      = settings['nfs_vms']
RESTAPI    = settings['restapi']
CLIENTS    = settings['client_vms']
SUBNET     = settings['subnet']
BOX        = settings['vagrant_box']
BOX_URL    = settings['vagrant_box_url']
MEMORY     = settings['memory']
STORAGECTL = settings['vagrant_storagectl']
ETH        = settings['eth']
DOCKER     = settings['docker']

if BOX == 'openstack'
  require 'vagrant-openstack-provider'
  OSVM = true
  USER = settings['os_ssh_username']
  OSUSER = settings['os_username']
  OSPREFIX = "#{OSUSER}-"
else
  OSVM = false
  OSPREFIX = ""
end

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
    'mons'        => (0..NMONS - 1).map { |j| "#{OSPREFIX}mon#{j}" },
    'osds'        => (0..NOSDS - 1).map { |j| "#{OSPREFIX}osd#{j}" },
    'mdss'        => (0..NMDSS - 1).map { |j| "#{OSPREFIX}mds#{j}" },
    'rgws'        => (0..NRGWS - 1).map { |j| "#{OSPREFIX}rgw#{j}" },
    'nfss'        => (0..NNFSS - 1).map { |j| "#{OSPREFIX}nfs#{j}" },
    'clients'     => (0..CLIENTS - 1).map { |j| "#{OSPREFIX}client#{j}" }
  }

  if RESTAPI then
    ansible.groups['restapis'] = (0..NMONS - 1).map { |j| "#{OSPREFIX}mon#{j}" }
  end


  # In a production deployment, these should be secret
  if DOCKER then
    ansible.extra_vars = {
      mon_containerized_deployment: 'true',
      osd_containerized_deployment: 'true',
      mds_containerized_deployment: 'true',
      rgw_containerized_deployment: 'true',
      nfs_containerized_deployment: 'true',
      restapi_containerized_deployment: 'true',
      ceph_mon_docker_interface: ETH,
      ceph_mon_docker_subnet: "#{SUBNET}.0/24",
      ceph_osd_docker_extra_env: "CEPH_DAEMON=OSD_CEPH_DISK,OSD_JOURNAL_SIZE=100",
      cluster_network: "#{SUBNET}.0/24",
      public_network: "#{SUBNET}.0/24",
      ceph_osd_docker_devices: settings['disks'],
      # Note that OSVM is defaulted to false above
      ceph_docker_on_openstack: OSVM,
      ceph_rgw_civetweb_port: 8080
    }
  else
    ansible.extra_vars = {
      "ceph_#{settings['ceph_install_source']}"=> 'true',
      journal_collocation: 'true',
      pool_default_size: '2',
      journal_size: 100,
      monitor_interface: ETH,
      cluster_network: "#{SUBNET}.0/24",
      public_network: "#{SUBNET}.0/24",
      devices: settings['disks'],
      os_tuning_params: settings['os_tuning_params']
    }
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

  # Faster bootup.  Disable if you need this for libvirt
  config.vm.provider :libvirt do |v,override|
    override.vm.synced_folder '.', '/home/vagrant/sync', disabled: true
  end

  if BOX == 'openstack'
    # OpenStack VMs
    config.vm.provider :openstack do |os|
      config.vm.synced_folder ".", "/home/#{USER}/vagrant", disabled: true
      config.ssh.username = USER
      config.ssh.private_key_path = settings['os_ssh_private_key_path']
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
      config.vm.provision "shell", inline: "true", upload_path: "/home/#{USER}/vagrant-shell"
    end
  end

  (0..CLIENTS - 1).each do |i|
    config.vm.define "#{OSPREFIX}client#{i}" do |client|
      client.vm.hostname = "#{OSPREFIX}ceph-client#{i}"
      if !OSVM
        client.vm.network :private_network, ip: "#{SUBNET}.4#{i}"
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
      end

      # Parallels
      client.vm.provider "parallels" do |prl|
        prl.name = "ceph-client#{i}"
        prl.memory = "#{MEMORY}"
      end
    end
  end

  (0..NRGWS - 1).each do |i|
    config.vm.define "#{OSPREFIX}rgw#{i}" do |rgw|
      rgw.vm.hostname = "#{OSPREFIX}ceph-rgw#{i}"
      if !OSVM
        rgw.vm.network :private_network, ip: "#{SUBNET}.5#{i}"
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
      end

      # Parallels
      rgw.vm.provider "parallels" do |prl|
        prl.name = "ceph-rgw#{i}"
        prl.memory = "#{MEMORY}"
      end
    end
  end

  (0..NNFSS - 1).each do |i|
    config.vm.define "nfs#{i}" do |nfs|
      nfs.vm.hostname = "ceph-nfs#{i}"
      if !OSVM
        nfs.vm.network :private_network, ip: "#{SUBNET}.6#{i}"
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
      end

      # Parallels
      nfs.vm.provider "parallels" do |prl|
        prl.name = "ceph-nfs#{i}"
        prl.memory = "#{MEMORY}"
      end
    end
  end

  (0..NMDSS - 1).each do |i|
    config.vm.define "#{OSPREFIX}mds#{i}" do |mds|
      mds.vm.hostname = "#{OSPREFIX}ceph-mds#{i}"
      if !OSVM
        mds.vm.network :private_network, ip: "#{SUBNET}.7#{i}"
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
      end
      # Parallels
      mds.vm.provider "parallels" do |prl|
        prl.name = "ceph-mds#{i}"
        prl.memory = "#{MEMORY}"
      end
    end
  end

  (0..NMONS - 1).each do |i|
    config.vm.define "#{OSPREFIX}mon#{i}" do |mon|
      mon.vm.hostname = "#{OSPREFIX}ceph-mon#{i}"
      if !OSVM
        mon.vm.network :private_network, ip: "#{SUBNET}.1#{i}"
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
      end

      # Parallels
      mon.vm.provider "parallels" do |prl|
        prl.name = "ceph-mon#{i}"
        prl.memory = "#{MEMORY}"
      end
    end
  end

  (0..NOSDS - 1).each do |i|
    config.vm.define "#{OSPREFIX}osd#{i}" do |osd|
      osd.vm.hostname = "#{OSPREFIX}ceph-osd#{i}"
      if !OSVM
        osd.vm.network :private_network, ip: "#{SUBNET}.10#{i}"
        osd.vm.network :private_network, ip: "#{SUBNET}.20#{i}"
      end
      # Virtualbox
      osd.vm.provider :virtualbox do |vb|
        (0..1).each do |d|
          vb.customize ['createhd',
                        '--filename', "disk-#{i}-#{d}",
                        '--size', '11000'] unless File.exist?("disk-#{i}-#{d}.vdi")
          # Controller names are dependent on the VM being built.
          # It is set when the base box is made in our case ubuntu/trusty64.
          # Be careful while changing the box.
          vb.customize ['storageattach', :id,
                        '--storagectl', STORAGECTL,
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
      driverletters = ('b'..'z').to_a
      osd.vm.provider :libvirt do |lv|
        (0..1).each do |d|
          lv.storage :file, :device => "vd#{driverletters[d]}", :path => "disk-#{i}-#{d}.disk", :size => '11G'
        end
        lv.memory = MEMORY
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

      # Run the provisioner after the last machine comes up
      osd.vm.provision 'ansible', &ansible_provision if i == (NOSDS - 1)
    end
  end
end
