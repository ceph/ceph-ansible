# -*- mode: ruby -*-
# vi: set ft=ruby :


VAGRANTFILE_API_VERSION = "2"

NMONS = 3
NOSDS = 3

ansible_provision = Proc.new do |ansible|
  ansible.playbook = "site.yml"
  # Note: Can't do ranges like mon[0-2] in groups because
  # these aren't supported by Vagrant, see
  # https://github.com/mitchellh/vagrant/issues/3539
  ansible.groups = {
    "mons" => (0..NMONS-1).map {|j| "mon#{j}"},
    "osds" => (0..NOSDS-1).map {|j| "osd#{j}"},
    "mdss" => [],
    "rgws" => ["rgw"]
  }

  # In a production deployment, these should be secret
  ansible.extra_vars = {
   fsid: "4a158d27-f750-41d5-9e7f-26ce4c9d2d45",
   monitor_secret: "AQAWqilTCDh7CBAAawXt6kyTgLFCxSvJhTEmuw=="
  }
  ansible.limit = 'all'
end

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"


  config.vm.define :rgw do |rgw|
    rgw.vm.network :private_network, ip: "192.168.0.2"
    rgw.vm.host_name = "ceph-rgw"
    rgw.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--memory", "192"]
    end
  end

  (0..NMONS-1).each do |i|
    config.vm.define "mon#{i}" do |mon|
      mon.vm.hostname = "ceph-mon#{i}"
      mon.vm.network :private_network, ip: "192.168.0.1#{i}"
      mon.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "192"]
      end
    end
  end

  (0..NOSDS-1).each do |i|
    config.vm.define "osd#{i}" do |osd|
      osd.vm.hostname = "ceph-osd#{i}"
      osd.vm.network :private_network, ip: "192.168.0.10#{i}"
      osd.vm.network :private_network, ip: "192.168.0.20#{i}"
      (0..5).each do |d|
        osd.vm.provider :virtualbox do |vb|
          vb.customize [ "createhd", "--filename", "disk-#{i}-#{d}", "--size", "1000" ]
          vb.customize [ "storageattach", :id, "--storagectl", "SATA Controller", "--port", 3+d, "--device", 0, "--type", "hdd", "--medium", "disk-#{i}-#{d}.vdi" ]
          vb.customize ["modifyvm", :id, "--memory", "192"]
        end
      end

      # Run the provisioner after the last machine comes up
      if i == (NOSDS-1)
        osd.vm.provision "ansible", &ansible_provision
      end
    end
  end
end
