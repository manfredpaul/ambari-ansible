
https://github.com/seanorama/ansible-ambari

https://github.com/apache/ambari/blob/trunk/ambari-server/docs/api/v1/index.md

http://mail-archives.apache.org/mod_mbox/ambari-user/201709.mbox/browser

https://community.hortonworks.com/articles/2473/rolling-upgrade-express-upgrade-in-ambari.html

https://community.hortonworks.com/questions/76806/creating-ambari-stacks-on-a-new-install.html

Upgrade Guide

Prerequisites/ Assumptions:
1. The stack is supported by Ambari for upgrade i.e. the stack should be manually upgradable via Ambari.
2. The Ambari details like Ambari ip, port, login credentials, cluster name, etc. are available from end user.
3. The stack details like repository, version, OS version, upgrade type, etc. are available from end user.


Steps:
We are listing the Ambari rest APIs only which can be programed in any language. The user
inputs are marked with <> here. Following are steps and the respective Rest API/Curl
commands for upgrade:

1) Registering the Stack:
The first step is registering the new stack with Ambari. We used the following curl command
to do this and the corresponding json file format is:

               POST  http://<Ambari Ip>:<Ambari port>/api/v1/stacks/<New StackName>/versions/<Stack Version>/repository_versions

               {
               "RepositoryVersions":
               {
                              "repository_version": "<New_Stack_Repository_Version>",
                              "display_name": "<Stack_Display_Name>"
               },
               "operating_systems": [
               {
                              "OperatingSystems":
                              {
                                             "os_type": "<OS_Type_and_Version>"
                              },
                              "repositories":
                              [
                              {
                                             "Repositories":
                                             {
                                                            "repo_id": "<Stack_Repository_ID>",
                                                            "repo_name": "<Stack_Repository_Name>",
                                                            "base_url": "<Stack_Repository_Base_URL>"
                                             }
                              },
                              {
                                             "Repositories":
                                             {
                                                            "repo_id": "<Stack_Utils_Repository_ID>",
                                                            "repo_name": "<Stack_Utils_Repository_Name>",
                                                            "base_url": "<Stack_Utils_Repository_Base_URL>"
                                             }
                              }
                              ]
               }
               ]
               }

We check the response of this command to confirm that the registration is successfull or not.
If the stack is already registered then this step can return error. We ignore this particular
error.

2) Installing the Stack:
The next step is installing the new stack on each host. We used the following curl command
to do this and the corresponding json file format is:

               POST http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/stack_versions

               {
               "ClusterStackVersions":
               {
                              "stack": "<New_Stack_Name>",
                              "version": "<New_Stack_Version>",
                              "repository_version": "<New_Stack_Repository_Version>"
               }
               }

3) Check the status of Installation:
Since installation is a time-consuming process, so we continuously poll for the status of
the request (the request Id we got from the previous step) for failed or completed.
We used the following curl command to do this:

               GET http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/requests/<Install request ID>

4) Upgrade of stack:
Once the installation is completed successfully, we supply the command to Ambari for upgradeof stack.
We used the following curl command to do this and the corresponding json file format is:

               POST http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/upgrades

               {
               "Upgrade":
               {
                              "repository_version": "<New_Stack_Repository_Version>",
                              "upgrade_type" : "<Upgrade_Type_Rolling_or_Express>"
               }
               }

5) Check status of Upgrade:
We continuously check for the upgrade item status for failed or holding.
During upgrade, there are multiple instances where the upgrade task will go for HOLDING (which
usually means Ambari need user intervention)
Example: During YARN upgrade, AMBARI will ask user if the YARN job queues are stopped/started.
When an upgrade_item goes to Holding status, we check the context of the upgrade_item and
take necessary action (Complete/Abort the upgrade_item) to automate the progress of upgrade.
We do this polling till the upgrade task goes on Holding for Finalize/Downgrade state. We
used the following curl command to do this:

               GET http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/upgrades?upgrade_groups/upgrade_items/UpgradeItem/status=HOLDING

and check the context of holding upgrade item.

6) Downgrade or Finalize:
Once the upgrade is successful, Ambari upgrade goes to Holding state. In this step, the end
user have a choice to either Downgrade the stack OR Finalize the upgrade.
We take the user action on this and progress accordingly.

For Downgrade:
Once the user chooses to downgrade, we first abort the existing upgrade task which is in holding
state by issuing following command:

               POST http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/upgrades/<Upgrade id>

               {
               "Upgrade":
               {
                              "request_status":"ABORTED",
                              "suspended":true
               }
               }

Then we issue a new downgrade request as follows:

               POST http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Clustername>/upgrades?downgrade=true

               {
               "Upgrade":
               {
                              "from_version": "<Old_Stack_Version>",
                              "repository_version": "<Old_Stack_Repository_Version>",
                              "direction": "DOWNGRADE",
                              "upgrade_type": "<Upgrade_Type_Rolling_or_Express>"
               }
               }

For Finalize:
Once the user chooses to finalize the stack, we complete the upgrade_item, which is in holding
state by following command:

               POST http://<Ambari Ip>:<Ambari port>/api/v1/clusters/<Cluster
name>/upgrades/<Upgrade id>/upgrade_groups/<Upgrade_group id>/upgrade_items/<Upgrade_item
id>

               {
               "UpgradeItem":
               {
                              "status":"COMPLETED"
               }
               }



Thanks and Regards
Arka Chattopadhyay

