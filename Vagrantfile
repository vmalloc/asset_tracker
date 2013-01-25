# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.define :client do |client_config|
      client_config.vm.box = "precise64"
      client_config.vm.box_url = "http://files.vagrantup.com/precise64.box"
      client_config.vm.host_name = "server"
      client_config.vm.provision :shell, :inline => "echo -e '12345678\\n12345678' | sudo passwd vagrant 2>/dev/null"
  end
end
