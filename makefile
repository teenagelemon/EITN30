base:  
		chmod +x forward.sh
		sudo ./forward.sh
		sudo python3 main.py  --base 0

mobile: 
		chmod +x iptables_mobile.sh
		sudo ./iptables_mobile.sh
		sudo python3 main.py --base 1
		
