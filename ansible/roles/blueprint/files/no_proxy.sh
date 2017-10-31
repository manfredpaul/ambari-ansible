#!/usr/bin/env bash

declare -a files=( "/var/lib/ambari-agent/cache/custom_actions/templates/repo_suse_rhel.j2"
                   "/var/lib/ambari-agent/cache/stacks/HDP/2.0.6/hooks/before-INSTALL/templates/repo_suse_rhel.j2"
                   "/var/lib/ambari-server/resources/custom_actions/templates/repo_suse_rhel.j2"
                   "/var/lib/ambari-server/resources/stacks/HDP/2.0.6/hooks/before-INSTALL/templates/repo_suse_rhel.j2"
)


for i in "${files[@]}"; do
  if [[ -f $i ]]; then
    already_done=`cat $i | grep "proxy=_none_"`
    echo $already_done
    if [ "x" != "x$already_done" ]; then
      echo "already patched"
    else
      echo "not yet patched. patching file $i"
      echo "proxy=_none_" >> $i
    fi
  fi
done