# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

NMONS = 3
NOSDS = 3

ansible_provision = proc do |ansible|
  ansible.playbook = 'site.yml'
  # Note: Can't do ranges like mon[0-2] in groups because
  # these aren't supported by Vagrant, see
  # https://github.com/mitchellh/vagrant/issues/3539
  ansible.groups = {
    'mons' => (0..NMONS - 1).map { |j| "mon#{j}" },
    'osds' => (0..NOSDS - 1).map { |j| "osd#{j}" },
    'mdss' => [],
    'rgws' => ['rgw']
  }

  # In a production deployment, these should be secret
  ansible.extra_vars = {
    fsid: '4a158d27-f750-41d5-9e7f-26ce4c9d2d45',
    monitor_secret: 'AQAWqilTCDh7CBAAawXt6kyTgLFCxSvJhTEmuw=='
  }
  ansible.limit = 'all'
end

def create_vmdk(name, size)
  dir = Pathname.new(__FILE__).expand_path.dirname
  path = File.join(dir, '.vagrant', name + '.vmdk')
  if !File.exist?(path) then system("vmware-vdiskmanager -c -s #{size} -t 0 -a scsi #{path} \
                                     2>&1 > /dev/null")
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = 'hashicorp/precise64'

  config.vm.define :rgw do |rgw|
    rgw.vm.network :private_network, ip: '192.168.42.2'
    rgw.vm.host_name = 'ceph-rgw'
    rgw.vm.provider :virtualbox do |vb|
      vb.customize ['modifyvm', :id, '--memory', '192']
    end
    rgw.vm.provider :vmware_fusion do |v|
      v.vmx['memsize'] = '192'
    end
  end

  (0..NMONS - 1).each do |i|
    config.vm.define "mon#{i}" do |mon|
      mon.vm.hostname = "ceph-mon#{i}"
      mon.vm.network :private_network, ip: "192.168.42.1#{i}"
      mon.vm.provider :virtualbox do |vb|
        vb.customize ['modifyvm', :id, '--memory', '192']
      end
      mon.vm.provider :vmware_fusion do |v|
        v.vmx['memsize'] = '192'
      end
    end
  end

  (0..NOSDS - 1).each do |i|
    config.vm.define "osd#{i}" do |osd|
      osd.vm.hostname = "ceph-osd#{i}"
      osd.vm.network :private_network, ip: "192.168.42.10#{i}"
      osd.vm.network :private_network, ip: "192.168.42.20#{i}"
      osd.vm.provider :virtualbox do |vb|
        (0..1).each do |d|
          vb.customize ['createhd',
                        '--filename', "disk-#{i}-#{d}",
                        '--size', '11000']
          vb.customize ['storageattach', :id,
                        '--storagectl', 'SATA Controller',
                        '--port', 3 + d,
                        '--device', 0,
                        '--type', 'hdd',
                        '--medium', "disk-#{i}-#{d}.vdi"]
        end
        vb.customize ['modifyvm', :id, '--memory', '192']
      end
      osd.vm.provider :vmware_fusion do |v|
        (0..1).each do |d|
          v.vmx["scsi0:#{d + 1}.present"] = 'TRUE'
          v.vmx["scsi0:#{d + 1}.fileName"] =
            create_vmdk("disk-#{i}-#{d}", '11000MB')
        end
        v.vmx['memsize'] = '192'
      end

      # Run the provisioner after the last machine comes up
      osd.vm.provision 'ansible', &ansible_provision if i == (NOSDS - 1)
    end
  end
end
