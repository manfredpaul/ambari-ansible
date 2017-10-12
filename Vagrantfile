# Defines our Vagrant environment
#
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  # create admin 
  config.vm.define :admin do |admin_config|
    admin_config.vm.box = "timveil/centos6.6-hdp-base"

    # admin_config.vm.hostname = "admin"
    admin_config.vm.define "admin.hdp.local"
    admin_config.vm.network :private_network, ip: "192.168.7.111", hostsupdater: "skip"
    admin_config.vm.provider "virtualbox" do |vb|
      vb.memory = "512"
      vb.name = "admin.hdp.local"
    end

    if Vagrant.has_plugin?("vagrant-vbguest")	      
      admin_config.vbguest.auto_update = true
      admin_config.vbguest.no_remote = true
      admin_config.vbguest.no_install = false
    end

    if Vagrant.has_plugin?("vagrant-proxyconf")
      admin_config.proxy.http     = ""
      admin_config.proxy.https    = ""
      admin_config.proxy.no_proxy = ""
    end	      
  end

  # namenode 1 - 2
  (1..2).each do |i|
    config.vm.define "nn#{i}" do |nn_config|
      nn_config.vm.box = "timveil/centos6.6-hdp-base"
      
      #nn_config.vm.hostname = "nn#{i}.hdp.local"
      nn_config.vm.define "nn#{i}.hdp.local"
      nn_config.vm.network :private_network, ip: "192.168.7.12#{i}", hostsupdater: "skip"
      nn_config.vm.provider "virtualbox" do |vb|
        vb.memory = "2048"
	    vb.name = "nn#{i}.hdp.local"
      end

      if Vagrant.has_plugin?("vagrant-vbguest")
        nn_config.vbguest.auto_update = true
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
      
      #dn_config.vm.hostname = "dn#{i}.hdp.local"
      dn_config.vm.define "dn#{i}.hdp.local"
      dn_config.vm.network :private_network, ip: "192.168.7.13#{i}", hostsupdater: "skip"
      dn_config.vm.provider "virtualbox" do |vb|
        vb.memory = "4096"
	    vb.name = "dn#{i}.hdp.local"
      end

      if Vagrant.has_plugin?("vagrant-vbguest")
        dn_config.vbguest.auto_update = true
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
    mgmt_config.vm.box = "timveil/centos7-hdp-base"

    #mgmt_config.vm.hostname = "mgmt.hdp.local"
    mgmt_config.vm.define "mgmt.hdp.local"
    mgmt_config.vm.network :private_network, ip: "192.168.7.110", hostsupdater: "skip"
    mgmt_config.vm.provider "virtualbox" do |vb|
      vb.memory = "256"
	  vb.name = "mgmt.hdp.local"
    end

    if Vagrant.has_plugin?("vagrant-vbguest")
      mgmt_config.vbguest.auto_update = true
      mgmt_config.vbguest.no_remote = true
      mgmt_config.vbguest.no_install = false
    end

    if Vagrant.has_plugin?("vagrant-proxyconf")
      mgmt_config.proxy.http     = ""
      mgmt_config.proxy.https    = ""
      mgmt_config.proxy.no_proxy = ""
    end

    mgmt_config.vm.provision "ansible" do |ansible|
        ansible.inventory_path = "ansible/inventory.ini"
        ansible.verbose = "vvv"
        ansible.sudo = true
        ansible.playbook = "ansible/main.yml"
        ansible.extra_vars = { ansible_ssh_user: 'vagrant' }
        ansible.limit = 'all'
    end
  end
end
