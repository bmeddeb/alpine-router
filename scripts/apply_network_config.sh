#!/bin/sh
# scripts/apply_network_config.sh

# Get parameters
INTERFACE=$1
IS_WAN=$2
DHCP_ENABLED=$3
STATIC_IP=$4
STATIC_NETMASK=$5
STATIC_GATEWAY=$6
DNS_SERVERS=$7

# Apply network configuration
if [ "$IS_WAN" = "True" ]; then
    echo "Configuring $INTERFACE as WAN interface"

    if [ "$DHCP_ENABLED" = "True" ]; then
        # Configure interface for DHCP
        cat > /etc/network/interfaces.d/$INTERFACE <<EOF
auto $INTERFACE
iface $INTERFACE inet dhcp
EOF
    else
        # Configure interface with static IP
        cat > /etc/network/interfaces.d/$INTERFACE <<EOF
auto $INTERFACE
iface $INTERFACE inet static
    address $STATIC_IP
    netmask $STATIC_NETMASK
    gateway $STATIC_GATEWAY
EOF

# Configure DNS servers
        if [ -n "$DNS_SERVERS" ]; then
            echo "Configuring DNS servers: $DNS_SERVERS"
            rm -f /etc/resolv.conf
            for dns in $(echo $DNS_SERVERS | tr ',' ' '); do
                echo "nameserver $dns" >> /etc/resolv.conf
            done
        fi
    fi
else
    echo "Configuring $INTERFACE as LAN interface"

    # Configure interface with static IP
    cat > /etc/network/interfaces.d/$INTERFACE <<EOF
auto $INTERFACE
iface $INTERFACE inet static
    address $STATIC_IP
    netmask $STATIC_NETMASK
EOF

    # If DHCP is enabled, configure dnsmasq
    if [ "$DHCP_ENABLED" = "True" ]; then
        echo "Enabling DHCP server on $INTERFACE"

        # Ensure dnsmasq is installed
        if ! command -v dnsmasq >/dev/null 2>&1; then
            echo "Installing dnsmasq..."
            apk add dnsmasq
        fi

        # Configure dnsmasq for this interface
        cat > /etc/dnsmasq.d/$INTERFACE.conf <<EOF
interface=$INTERFACE
dhcp-range=192.168.1.100,192.168.1.200,12h
dhcp-option=option:router,$STATIC_IP
EOF

        # Enable and start dnsmasq
        rc-update add dnsmasq default
        rc-service dnsmasq restart
    fi
fi

# Restart networking
echo "Restarting network service..."
rc-service networking restart

echo "Network configuration applied successfully for $INTERFACE"
exit 0