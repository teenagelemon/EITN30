sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT DROP

sudo iptables -A INPUT -i tun0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A OUTPUT -o tun0 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT

