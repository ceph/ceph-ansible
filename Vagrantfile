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
CLIENTS    = settings['client_vms']
SUBNET     = settings['subnet']
BOX        = settings['vagrant_box']
MEMORY     = settings['memory']
STORAGECTL = settings['vagrant_storagectl']
ETH        = settings['eth']

ansible_provision = proc do |ansible|
  ansible.playbook = 'site.yml'
  # Note: Can't do ranges like mon[0-2] in groups because
  # these aren't supported by Vagrant, see
  # https://github.com/mitchellh/vagrant/issues/3539
  ansible.groups = {
    'mons'        => (0..NMONS - 1).map { |j| "mon#{j}" },
    'restapis'    => (0..NMONS - 1).map { |j| "mon#{j}" },
    'osds'        => (0..NOSDS - 1).map { |j| "osd#{j}" },
    'mdss'        => (0..NMDSS - 1).map { |j| "mds#{j}" },
    'rgws'        => (0..NRGWS - 1).map { |j| "rgw#{j}" },
    'clients'     => (0..CLIENTS - 1).map { |j| "client#{j}" }
  }

  # In a production deployment, these should be secret
  ansible.extra_vars = {
    ceph_stable: 'true',
    journal_collocation: 'true',
    journal_size: 100,
    monitor_interface: ETH,
    cluster_network: "#{SUBNET}.0/24",
    public_network: "#{SUBNET}.0/24",
    devices: settings['disks'],
    os_tuning_params: settings['os_tuning_params']
  }
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
  config.ssh.insert_key = false # workaround for https://github.com/mitchellh/vagrant/issues/5048

  # Faster bootup.  Disable if you need this for libvirt
  config.vm.provider :libvirt do |v,override|
    override.vm.synced_folder '.', '/home/vagrant/sync', disabled: true
  end

  (0..CLIENTS - 1).each do |i|
    config.vm.define "client#{i}" do |client|
      client.vm.hostname = "ceph-client#{i}"
      client.vm.network :private_network, ip: "#{SUBNET}.4#{i}"

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
    end
  end

  (0..NRGWS - 1).each do |i|
    config.vm.define "rgw#{i}" do |rgw|
      rgw.vm.hostname = "ceph-rgw#{i}"
      rgw.vm.network :private_network, ip: "#{SUBNET}.4#{i}"

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
    end
  end

  (0..NMDSS - 1).each do |i|
    config.vm.define "mds#{i}" do |mds|
      mds.vm.hostname = "ceph-mds#{i}"
      mds.vm.network :private_network, ip: "#{SUBNET}.7#{i}"

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
    end
  end

  (0..NMONS - 1).each do |i|
    config.vm.define "mon#{i}" do |mon|
      mon.vm.hostname = "ceph-mon#{i}"
      mon.vm.network :private_network, ip: "#{SUBNET}.1#{i}"

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
    end
  end

  (0..NOSDS - 1).each do |i|
    config.vm.define "osd#{i}" do |osd|
      osd.vm.hostname = "ceph-osd#{i}"
      osd.vm.network :private_network, ip: "#{SUBNET}.10#{i}"
      osd.vm.network :private_network, ip: "#{SUBNET}.20#{i}"

      # Virtualbox
      osd.vm.provider :virtualbox do |vb|
        (0..1).each do |d|
          vb.customize ['createhd',
                        '--filename', "disk-#{i}-#{d}",
                        '--size', '11000']
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

      # Run the provisioner after the last machine comes up
      osd.vm.provision 'ansible', &ansible_provision if i == (NOSDS - 1)
    end
  end
end
