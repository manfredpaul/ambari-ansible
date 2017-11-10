# Defines our Vagrant environment
#
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # admin
  config.vm.define :admin do |admin_config|
    admin_config.vm.box = "timveil/centos6.6-hdp-base"

    # admin_config.vm.hostname = "admin"
    admin_config.vm.define "admin"
    admin_config.vm.network :private_network, ip: "192.168.7.111", hostsupdater: "skip"
    admin_config.vm.provider "virtualbox" do |vb|
      vb.memory = "2048"
      vb.name = "admin"
    end

    if Vagrant.has_plugin?("vagrant-vbguest")	      
      admin_config.vbguest.auto_update = false
      admin_config.vbguest.no_remote = true
      admin_config.vbguest.no_install = false
    end

    if Vagrant.has_plugin?("vagrant-proxyconf")
      admin_config.proxy.http     = ""
      admin_config.proxy.https    = ""
      admin_config.proxy.no_proxy = ""
    end	      
  end

  # repo
  config.vm.define :repo do |repo_config|
    repo_config.vm.box = "timveil/centos6.6-hdp-base"

    # repo_config.vm.hostname = "repo"
    repo_config.vm.define "repo"
    repo_config.vm.network :private_network, ip: "192.168.7.101", hostsupdater: "skip"
    repo_config.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
      vb.name = "repo"
    end

    if Vagrant.has_plugin?("vagrant-vbguest")
      repo_config.vbguest.auto_update = false
      repo_config.vbguest.no_remote = true
      repo_config.vbguest.no_install = false
    end

    if Vagrant.has_plugin?("vagrant-proxyconf")
      repo_config.proxy.http     = ""
      repo_config.proxy.https    = ""
      repo_config.proxy.no_proxy = ""
    end

    repo_config.vm.synced_folder "C:\\dev\\repo", "/var/www/html"
  end

  # namenode 1 - 2
  (1..2).each do |i|
    config.vm.define "nn#{i}" do |nn_config|
      nn_config.vm.box = "timveil/centos6.6-hdp-base"
      
      #nn_config.vm.hostname = "nn#{i}"
      nn_config.vm.define "nn#{i}"
      nn_config.vm.network :private_network, ip: "192.168.7.12#{i}", hostsupdater: "skip"
      nn_config.vm.provider "virtualbox" do |vb|
        vb.memory = "2048"
	    vb.name = "nn#{i}"
      end

      if Vagrant.has_plugin?("vagrant-vbguest")
        nn_config.vbguest.auto_update = false
        nn_config.vbguest.no_remote = true
        nn_config.vbguest.no_install = false
      end

      if Vagrant.has_plugin?("vagrant-proxyconf")
        nn_config.proxy.http     = ""
        nn_config.proxy.https    = ""
        nn_config.proxy.no_proxy = ""
      end

    end
  end

  # datanode 1 - 3
  (1..3).each do |i|
    config.vm.define "dn#{i}" do |dn_config|
      dn_config.vm.box = "timveil/centos6.6-hdp-base"
      
      #dn_config.vm.hostname = "dn#{i}"
      dn_config.vm.define "dn#{i}"
      dn_config.vm.network :private_network, ip: "192.168.7.13#{i}", hostsupdater: "skip"
      dn_config.vm.provider "virtualbox" do |vb|
        vb.memory = "16384"
	    vb.name = "dn#{i}"
      end

      if Vagrant.has_plugin?("vagrant-vbguest")
        dn_config.vbguest.auto_update = false
        dn_config.vbguest.no_remote = true
        dn_config.vbguest.no_install = false
      end

      if Vagrant.has_plugin?("vagrant-proxyconf")
        dn_config.proxy.http     = ""
        dn_config.proxy.https    = ""
        dn_config.proxy.no_proxy = ""
      end
    end
  end

  # create mgmt node
  config.vm.define :mgmt do |mgmt_config|
    mgmt_config.vm.box = "timveil/centos6.6-hdp-base"

    #mgmt_config.vm.hostname = "mgmt"
    mgmt_config.vm.define "mgmt"
    mgmt_config.vm.network :private_network, ip: "192.168.7.110", hostsupdater: "skip"
    mgmt_config.vm.provider "virtualbox" do |vb|
      vb.memory = "1024"
	  vb.name = "mgmt"
    end

    if Vagrant.has_plugin?("vagrant-vbguest")
      mgmt_config.vbguest.auto_update = false
      mgmt_config.vbguest.no_remote = true
      mgmt_config.vbguest.no_install = false
    end

    if Vagrant.has_plugin?("vagrant-proxyconf")
      mgmt_config.proxy.http     = ""
      mgmt_config.proxy.https    = ""
      mgmt_config.proxy.no_proxy = ""
    end

    mgmt_config.vm.provision "Install", type: "shell", path: "install.sh"
  end
end
