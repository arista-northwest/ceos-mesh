# ceos-mesh
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
      
