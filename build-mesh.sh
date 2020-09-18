
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


create_ceos 0.1
create_ceos 0.0
create_ceos 1.0
create_ceos 1.1
connect_ceos 0.1 1.1 eth2 eth4
connect_ceos 0.1 0.0 eth3 eth1
connect_ceos 0.0 0.1 eth1 eth3
connect_ceos 0.0 1.0 eth2 eth4
connect_ceos 1.0 1.1 eth1 eth3
connect_ceos 1.0 0.0 eth4 eth2
connect_ceos 1.1 1.0 eth3 eth1
connect_ceos 1.1 0.1 eth4 eth2
sudo docker unpause 0.1
sudo docker unpause 0.0
sudo docker unpause 1.0
sudo docker unpause 1.1
