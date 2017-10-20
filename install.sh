#!/bin/sh

echo " "
echo "---------------------------------------------------------------------------------------------------------------"
echo "----- running yum update"
echo "---------------------------------------------------------------------------------------------------------------"
echo " "

yum update -y && yum clean all

echo " "
echo "---------------------------------------------------------------------------------------------------------------"
echo "----- install ansible"
echo "---------------------------------------------------------------------------------------------------------------"
echo " "

yum install -y ansible && yum clean all

