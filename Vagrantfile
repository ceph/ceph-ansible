# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'yaml'
VAGRANTFILE_API_VERSION = '2'

config_file=File.expand_path(File.join(File.dirname(__FILE__), 'vagrant_variables.yml'))
settings=YAML.load_file(config_file)

_shellScript = "pull-roles.sh"
system("sh #{_shellScript}")

NMONS      = settings['mon_vms']
NOSDS      = settings['osd_vms']
NMDSS      = settings['mds_vms']
NRGWS      = settings['rgw_vms']
CLIENTS    = settings['client_vms']
SUBNET     = settings['subnet']
BOX        = settings['vagrant_box']
MEMORY     = settings['memory']
STORAGECTL = settings['vagrant_storagectl']

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
    fsid: '4a158d27-f750-41d5-9e7f-26ce4c9d2d45',
    monitor_secret: 'AQAWqilTCDh7CBAAawXt6kyTgLFCxSvJhTEmuw==',
    journal_size: 100,
    monitor_interface: 'eth1',
    cluster_network: "#{SUBNET}.0/24",
    public_network: "#{SUBNET}.0/24",
    devices: "[ '/dev/sdb', '/dev/sdc' ]",
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

  (0..CLIENTS - 1).each do |i|
    config.vm.define "client#{i}" do |client|
      client.vm.hostname = "ceph-client#{i}"
      client.vm.network :private_network, ip: "#{SUBNET}.4#{i}"
      client.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end
      client.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end
    end
  end

  (0..NRGWS - 1).each do |i|
    config.vm.define "rgw#{i}" do |rgw|
      rgw.vm.hostname = "ceph-rgw#{i}"
      rgw.vm.network :private_network, ip: "#{SUBNET}.4#{i}"
      rgw.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end
      rgw.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end
    end
  end

  (0..NMDSS - 1).each do |i|
    config.vm.define "mds#{i}" do |rgw|
      rgw.vm.hostname = "ceph-mds#{i}"
      rgw.vm.network :private_network, ip: "#{SUBNET}.7#{i}"
      rgw.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end
      rgw.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end
    end
  end

  (0..NMONS - 1).each do |i|
    config.vm.define "mon#{i}" do |mon|
      mon.vm.hostname = "ceph-mon#{i}"
      mon.vm.network :private_network, ip: "#{SUBNET}.1#{i}"
      mon.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', "#{MEMORY}"]
      end
      mon.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = "#{MEMORY}"
      end
    end
  end

  (0..NOSDS - 1).each do |i|
    config.vm.define "osd#{i}" do |osd|
      osd.vm.hostname = "ceph-osd#{i}"
      osd.vm.network :private_network, ip: "#{SUBNET}.10#{i}"
      osd.vm.network :private_network, ip: "#{SUBNET}.20#{i}"
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
      osd.vm.provider :vmware_fusion do |v|
        (0..1).each do |d|
          v.vmx["scsi0:#{d + 1}.present"] = 'TRUE'
          v.vmx["scsi0:#{d + 1}.fileName"] =
            create_vmdk("disk-#{i}-#{d}", '11000MB')
        end
        v.vmx['memsize'] = "#{MEMORY}"
      end

      # Run the provisioner after the last machine comes up
      osd.vm.provision 'ansible', &ansible_provision if i == (NOSDS - 1)
    end
  end
end
