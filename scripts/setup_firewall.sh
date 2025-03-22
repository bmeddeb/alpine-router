#!/bin/sh
# scripts/setup_firewall.sh

# Get parameters
WAN_INTERFACE=$1
LAN_INTERFACES=$2  # Comma-separated list of LAN interfaces

# Ensure iptables and iptables-persistent are installed
apk add iptables ip6tables

# Clear existing rules
iptables -F
iptables -t nat -F
iptables -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow LAN to WAN forwarding
for lan in $(echo $LAN_INTERFACES | tr ',' ' '); do
    iptables -A FORWARD -i $lan -o $WAN_INTERFACE -j ACCEPT
done

# Allow packets from established connections
iptables -A FORWARD -i $WAN_INTERFACE -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Set up NAT for LAN clients
for lan in $(echo $LAN_INTERFACES | tr ',' ' '); do
    iptables -t nat -A POSTROUTING -o $WAN_INTERFACE -s $(ip -o -f inet addr show $lan | awk '{print $4}') -j MASQUERADE
done

# Allow SSH access from LAN
for lan in $(echo $LAN_INTERFACES | tr ',' ' '); do
    iptables -A INPUT -i $lan -p tcp --dport 22 -j ACCEPT
done

# Allow DNS and DHCP services on LAN
for lan in $(echo $LAN_INTERFACES | tr ',' ' '); do
    iptables -A INPUT -i $lan -p udp --dport 53 -j ACCEPT
    iptables -A INPUT -i $lan -p tcp --dport 53 -j ACCEPT
    iptables -A INPUT -i $lan -p udp --dport 67:68 -j ACCEPT
done

# Allow HTTP/HTTPS for management interface
for lan in $(echo $LAN_INTERFACES | tr ',' ' '); do
    iptables -A INPUT -i $lan -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -i $lan -p tcp --dport 443 -j ACCEPT
    iptables -A INPUT -i $lan -p tcp --dport 5000 -j ACCEPT  # Flask development server
done

# Save rules
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4

# Enable IP forwarding
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-router.conf
sysctl -p /etc/sysctl.d/99-router.conf

echo "Firewall configured successfully"
exit 0