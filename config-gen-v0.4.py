#!/usr/bin/env python
import os, sys, re, subprocess, stat, argparse, optparse

# Modified by: (please date changes)
# ariff@arista.com 05/23/2020
# urvish@arista.com 09/18/2020

"""
This script generates configuration files for isis nodes that have hostnames represented by their identity in the x y graph show below.
For example the node loopback IP for (0,0) will be 192.168.0.0 and the loopback for (1.0) will be 192.168.1.0.

Execute this script:
sudo python config-gen-v0.3.py 

Executing this script will result in the following files being created:
build-mesh.sh
delete-mesh.sh
configs/<node-id>

build-mesh.sh is a shell script that will contain all the neccessary docker configuration to instantiate and launch the number of nodes.
delete-mesh.sh is another shell script that will help tear down and delete the nodes (so we dont have to do it manually).

The configs/ directory will contain the startup-config files for all nodes being created so they pick up their config on boot-up.

With an adequately powered server, we can test whether the control plane will sustain a isis l2 network with upto 200x200 nodes. 
If we build beyond this, the script will have to be modified.  For this example, we are using a 2x2 matrix of nodes (4 total)

The rough target for v1.5 is 4K satellites.


       ^   +-----+     +-----+    +-----+
       |   | 0.2 +-----+ 1.2 +----+ 2.2 |
       |   +-----+     +-----+    +-----+
       |      |           |          |
       |   +-----+     +-----+    +-----+
     Y |   | 0.1 +-----+ 1.1 +----+ 2.1 |
       |   +-----+     +-----+    +-----+
       |      |           |          |
       |   +-----+     +-----+    +-----+
       |   | 0.0 +-----+ 1.0 +----+ 2.0 |
       +   +-----+     +-----+    +-----+

           +---------------------------->
                         X




"""


#print connections

# Config files use these mini confliglets.

startupConfigTemplateHostname = """hostname %s
"""

startupConfigTemplate = """!
interface Port-Channel1
   no switchport
   ip address unnumbered Loopback0
   isis enable ISL
   isis network point-to-point
!
interface Port-Channel2
   no switchport
   ip address unnumbered Loopback0
   isis enable ISL
   isis network point-to-point
!
interface Port-Channel3
   no switchport
   ip address unnumbered Loopback0
   isis enable ISL
   isis network point-to-point
!
interface Port-Channel4
   no switchport
   ip address unnumbered Loopback0
   isis enable ISL
   isis network point-to-point
!
interface Ethernet1
   channel-group 1 mode on
!
interface Ethernet2
   channel-group 2 mode on
!
interface Ethernet3
   channel-group 3 mode on
!
interface Ethernet4
   channel-group 4 mode on
!
service routing protocols model multi-agent
!
spanning-tree mode none
aaa authentication policy local allow-nopassword-remote-login
aaa authorization exec default local
!
ip routing
mpls ip
"""


startupConfigTemplateIntfLoopback = """!
interface Loopback0
   ip address %s/32
   node-segment ipv4 index %d
   isis enable ISL
"""

startupConfigTemplateISIS = """!
router isis ISL
   net %s
   is-type level-2
   log-adjacency-changes
   !
   address-family ipv4 unicast
   !
   segment-routing mpls
      no shutdown
!
"""
#----------------------------------------------------

dockerConfigFileTemplate = """
create_ceos(){
	sudo docker create --name=$1 --privileged -v ~/configs/$1/:/mnt/flash:Z -e INTFTYPE=eth -e ETBA=1 -e SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 -e CEOS=1 -e EOS_PLATFORM=ceoslab -e container=docker -i -t ceosimage:latest /sbin/init systemd.setenv=INTFTYPE=eth systemd.setenv=ETBA=1 systemd.setenv=SKIP_ZEROTOUCH_BARRIER_IN_SYSDBINIT=1 systemd.setenv=CEOS=1 systemd.setenv=EOS_PLATFORM=ceoslab systemd.setenv=container=docker
	sudo docker start $1
	sudo docker pause $1
}

connect_ceos() {
   echo "Connecting ${1}:${3} to ${2}:${4}"
   sudo mkdir -p /var/run/netns
   pid1="$(sudo docker inspect -f '{{.State.Pid}}' ${1})"
   pid2="$(sudo docker inspect -f '{{.State.Pid}}' ${2})"
   sudo ln -sf /proc/$pid1/ns/net /var/run/netns/$1
   sudo ln -sf /proc/$pid2/ns/net /var/run/netns/$2

   sudo ip link add $1-$3 type veth peer name $2-$4
   sudo ip link set $1-$3 netns $1
   sudo ip link set $2-$4 netns $2
   sudo ip netns exec $1 ip link set $1-$3 name $3
   sudo ip netns exec $2 ip link set $2-$4 name $4
   sudo ip netns exec $1 ip link set $3 up
   sudo ip netns exec $2 ip link set $4 up
}


"""


def generateStartupConfig(node, i):
   startupConfig = startupConfigTemplateHostname %(node)
   startupConfig += startupConfigTemplate
   startupConfig += startupConfigTemplateIntfLoopback %((nodes[node]['lo0']),i)
   startupConfig += startupConfigTemplateISIS % (nodes[node]['NET'])
   return startupConfig

def generateDockerConfig():
   dockerConfigFile = dockerConfigFileTemplate
   dockerConfigFileStopDelete = ''
   for node in nodes:
      dockerConfigFile += 'create_ceos ' + node + '\n'
   for i in connections:
      #dockerConfigFile += 'create_ceos ' +
      #device1 = connections[i][0]
      dockerConfigFile += 'connect_ceos '+ i + '\n'
   #print dockerConfigFile
   for node in nodes:
      dockerConfigFile += 'sudo docker unpause ' + node + '\n'
   return dockerConfigFile


def generateDockerStopDeleteConfig():
   dockerConfigFileStopDelete = ''
   for node in nodes:
      dockerConfigFileStopDelete +='sudo docker stop ' + node + '\n'
      dockerConfigFileStopDelete +='sudo docker rm ' + node + '\n'      
   #print dockerConfigFileStopDelete
   return dockerConfigFileStopDelete

class PlainHelpFormatter(optparse.IndentedHelpFormatter):
    def format_description(self, description):
        if description:
            return description + "\n"
        else:
            return ""

parser = optparse.OptionParser(
    prog='python config-gen-v0.4.py',
    formatter=PlainHelpFormatter(),
    description=u'''   
       ^   +-----+     +-----+    +-----+
       |   | 0.2 +-----+ 1.2 +----+ 2.2 |
       |   +-----+     +-----+    +-----+
       |      |           |          |
       |   +-----+     +-----+    +-----+
     Y |   | 0.1 +-----+ 1.1 +----+ 2.1 |
       |   +-----+     +-----+    +-----+
       |      |           |          |
       |   +-----+     +-----+    +-----+
       |   | 0.0 +-----+ 1.0 +----+ 2.0 |
       +   +-----+     +-----+    +-----+
           +---------------------------->
                        X
      Example: python config-gen-v0.4.py -x 2 -y 2 -c ceosimage:latest  
                        
      Executing this script will result in the following files being created:
      build-mesh.sh
      delete-mesh.sh
      configs/<node-id>
      
      
      build-mesh.sh is a shell script that will contain all the neccessary docker configuration to instantiate and launch the number of nodes.
delete-mesh.sh is another shell script that will help tear down and delete the nodes (so we dont have to do it manually).

      The configs/ directory will contain the startup-config files for all nodes being created so they pick up their config on boot-up.
      ''')
parser.add_option("-x", "--columns", type=int, default=2, help="Specify the number of columns in the network")
parser.add_option("-y", "--rows", type=int, default=2, help="Specify the number of rows in the network")
parser.add_option("-c", "--ceosimagename", default="ceosimage:latest", help="Specify ceos image name with tag")
args = parser.parse_args()

(opt,args) = parser.parse_args()

print(opt.rows)
print(opt.columns)

# Modify only these two parameters and then look for files created under configs/hostname.
x = opt.columns
y = opt.rows

nodes = {}
connections = []

for j in range(y):
   for i in range(x):
      nodeId = str(i) + "." + str(j)
      isisNETnumStrA = str(i)
      isisNETnumStrB = str(j)
      isisNETnumStrA = isisNETnumStrA.zfill(2)
      isisNETnumStrB = isisNETnumStrB.zfill(2)
      # print isisNETnumStrA+isisNETnumStrB
      nodes[nodeId] = {'1': 'eth1', '2': 'eth2', '3': 'eth3', '4': 'eth4', 'lo0': '192.168.%d.%d' % (i, j),
                       'NET': '49.0012.1000.0000.%s%s.00' % (isisNETnumStrA, isisNETnumStrB)}
      # print nodes[nodeId]
      # nodes defined

# used to debug above
# for i, n in enumerate(nodes):
#   nodes[n]={'lo0':loopbackAddrList[i]}


# now to map interfaces between nodes
# 1.1:1 1.2:3
# 1.1:2 2.1:4
# 1.1:3 1.0:1
# 1.1:4 0.1:2


for x in nodes:
   #print x
   s = x
   parts = s.split(".")
   a=parts[0]
   b=parts[1]
   #print a
   #print b
   #print a + "." + b
   #print (nodes[x])
   nodeSelf = a + "." + b
   #print "self "+ nodeSelf + " north int " + nodeSelfNorthIntf
   nodeNorth = a+"."+str(int(b)+1)
   nodeSelfNorthIntf = nodes[x]['1']
   if nodeNorth in nodes:
      nodeNorthInf = nodes[nodeNorth]['3']
      #print nodeSelf + " " + nodeSelfNorthIntf + " " + nodeNorth + " " + nodeNorthInf
      connections.append(nodeSelf + " " + nodeNorth + " " + nodeSelfNorthIntf + " " + nodeNorthInf)

   nodeEast = str(int(a)+1) + "." + b
   nodeSelfEastIntf = nodes[x]['2']
   if nodeEast in nodes:
      nodeEastInf = nodes[nodeEast]['4']
      #print nodeSelf + " " + nodeSelfEastIntf + " " + nodeEast + " " + nodeEastInf
      connections.append(nodeSelf + " " + nodeEast + " " + nodeSelfEastIntf + " " + nodeEastInf)

   nodeSouth = a + "." + str(int(b)-1)
   nodeSelfSouthIntf = nodes[x]['3']
   if nodeSouth in nodes:
      nodeSouthIntf = nodes[nodeSouth]['1']
      #print nodeSelf + " " + nodeSelfSouthIntf + " " + nodeSouth + " " + nodeSouthIntf
      connections.append(nodeSelf + " " + nodeSouth + " " + nodeSelfSouthIntf + " " + nodeSouthIntf)

   nodeWest = str(int(a)-1) + "." + b
   nodeSelfWestIntf = nodes[x]['4']
   if nodeWest in nodes:
      nodeWestIntf = nodes[nodeWest]['2']
      #print nodeSelf + " " + nodeSelfWestIntf + " " + nodeWest + " " + nodeWestIntf
      connections.append(nodeSelf + " " + nodeWest + " " + nodeSelfWestIntf + " " + nodeWestIntf)

dockerConfigFile = generateDockerConfig()
f=open('build-mesh.sh', 'w')
f.write( dockerConfigFile )
f.close()
os.chmod('build-mesh.sh', 0o0777)

dockerConfigDeleteFile = generateDockerStopDeleteConfig()
f=open('delete-mesh.sh', 'w')
f.write( dockerConfigDeleteFile )
f.close()
os.chmod('delete-mesh.sh', 0o0777)


for i, node in enumerate (nodes):
   #print x
   config = generateStartupConfig(node,i)
   #print config
   #path = '/Users/ariff/Documents/WorkArista/customers/starlink/containers/scripts/configs'
   path = 'configs'
   if not os.path.exists(path):
      os.makedirs(path)
   if not os.path.isdir('configs/%s' %node):
      os.mkdir('configs/%s' %node)
   f=open('configs/%s/startup-config' % node, 'w')
   f.write( config )
   f.close()



