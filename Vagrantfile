# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.define :client do |client_config|
      client_config.vm.box = "precise64"
      client_config.vm.box_url = "http://files.vagrantup.com/precise64.box"
      client_config.vm.host_name = "server"
  end
end
