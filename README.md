Requirements:
Linux Server
Install Docker and start it
Confirm Docker is working correctly:

[root@server ~]# sudo docker run hello-world
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
0e03bdcc26d7: Pull complete
Digest: sha256:d58e752213a51785838f9eed2b7a498ffa1cb3aa7f946dda11af39286c3db9a9
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/

[root@server ~]#



Steps to create a container based lab network:
Import the cEOS-lab docker image ( Note: This will take a few minutes )
The image can be downloaded from here : https://aristanetworks.egnyte.com/dl/ls77JnQBeq

[root@server ~]# sudo docker import cEOS-lab.tar.xz ceosimage:latest

Confirm that the image is imported

[root@server ~]# sudo docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
ceosimage           latest              3db8cb8c38e6        49 seconds ago      1.74GB

Execute the config-gen-vx.x.py script 

[root@server ~]# python config-gen-v0.4.py -h
Usage: python config-gen-v0.4.py [options]


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


Options:
  -h, --help            show this help message and exit
  -x COLUMNS, --columns=COLUMNS
                        Specify the number of columns in the network
  -y ROWS, --rows=ROWS  Specify the number of rows in the network
  -c CEOSIMAGENAME, --ceosimagename=CEOSIMAGENAME
                        Specify ceos image name with tag


[root@server ~]# python config-gen-v0.4.py -x 2 -y 2



Confirm that the files are created
[root@server ~]# ls
anaconda-ks.cfg  build-mesh.sh  cEOS-lab.tar.xz  config-gen-v0.4.py  configs  dead.letter  delete-mesh.sh
[root@server ~]# ls configs/
0.0  0.1  1.0  1.1
[root@server ~]#

Create the mesh

[root@server ~]# ./build-mesh.sh
afe4f3e20e42efc31a026ef68d619bde7667e1c0a3afccd276f905a7e07e8413
0.1
0.1
1cfe866808b4c1044f8b4ee4e9dcf976839bc9cbf0f92584af9cab4597d96f95
0.0
0.0
a59b4643074e095744d6258167f10d07a55ca877775592fe0b6164091321cb20
1.0
1.0
eb1cc5847ab27e3790100b39c3af19b4717b8cdebd15e2d0927745b16facc509
1.1
1.1
Connecting 0.1:eth2 to 1.1:eth4
Connecting 0.1:eth3 to 0.0:eth1
Connecting 0.0:eth1 to 0.1:eth3
RTNETLINK answers: File exists
RTNETLINK answers: File exists
Connecting 0.0:eth2 to 1.0:eth4
Connecting 1.0:eth1 to 1.1:eth3
Connecting 1.0:eth4 to 0.0:eth2
RTNETLINK answers: File exists
RTNETLINK answers: File exists
Connecting 1.1:eth3 to 1.0:eth1
RTNETLINK answers: File exists
RTNETLINK answers: File exists
Connecting 1.1:eth4 to 0.1:eth2
RTNETLINK answers: File exists
RTNETLINK answers: File exists
0.1
0.0
1.0
1.1

Confirm that the docker containers are created and the config is correctly applied

[root@server ~]# docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS                   PORTS               NAMES
eb1cc5847ab2        ceosimage:latest    "/sbin/init system..."   About a minute ago   Up About a minute                            1.1
a59b4643074e        ceosimage:latest    "/sbin/init system..."   About a minute ago   Up About a minute                            1.0
1cfe866808b4        ceosimage:latest    "/sbin/init system..."   About a minute ago   Up About a minute                            0.0
afe4f3e20e42        ceosimage:latest    "/sbin/init system..."   2 minutes ago        Up About a minute                            0.1
fa1fc537e35a        hello-world         "/hello"                 2 hours ago          Exited (0) 2 hours ago                       modest_swirles
[root@server ~]#


Log into the container

sudo docker exec -it 0.1 Cli
