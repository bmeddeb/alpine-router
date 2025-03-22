# interface_manager.py

from flask import Blueprint, jsonify, request, render_template, url_for, send_from_directory
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import subprocess
import json
import os

DATABASE_URL = 'sqlite:///alpine.db'

Base = declarative_base()

# Create static directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), 'static/css'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(__file__), 'static/js'), exist_ok=True)

class NetworkInterface(Base):
    __tablename__ = 'network_interfaces'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    label = Column(String, nullable=False, default='LAN')
    is_wan = Column(Boolean, default=False)
    dhcp_enabled = Column(Boolean, default=True)
    static_ip = Column(String)
    static_netmask = Column(String, default='255.255.255.0')
    static_gateway = Column(String)
    dns_servers = Column(String)

# Initialize database
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

interface_manager = Blueprint('interface_manager', __name__, 
                             static_folder='static',
                             template_folder='templates')

@interface_manager.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@interface_manager.route('/setup')
def interface_setup():
    """Render the interface setup page"""
    return render_template('interface_setup.html')

@interface_manager.route('/interfaces')
def list_interfaces():
    """Get all network interfaces with their configuration"""
    session = Session()

    # Run the hardware discovery to get current interfaces
    result = subprocess.run(
        ["../backend/target/debug/hardware_discovery"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return jsonify({"error": "Hardware discovery failed"}), 500

    interfaces = json.loads(result.stdout)

    # Merge with database configuration
    for iface in interfaces:
        db_iface = session.query(NetworkInterface).filter_by(name=iface['name']).first()
        if not db_iface:
            # Insert interface into DB with default settings
            db_iface = NetworkInterface(
                name=iface['name'],
                label='LAN',
                is_wan=False,
                dhcp_enabled=True
            )
            session.add(db_iface)
            session.commit()
            db_iface = session.query(NetworkInterface).filter_by(name=iface['name']).first()

        # Add configuration from database
        iface['label'] = db_iface.label
        iface['is_wan'] = db_iface.is_wan
        iface['dhcp_enabled'] = db_iface.dhcp_enabled
        iface['static_ip'] = db_iface.static_ip
        iface['static_netmask'] = db_iface.static_netmask
        iface['static_gateway'] = db_iface.static_gateway
        iface['dns_servers'] = db_iface.dns_servers

    return jsonify(interfaces)

@interface_manager.route('/interfaces/<name>', methods=['GET'])
def get_interface(name):
    """Get specific interface configuration"""
    session = Session()
    db_iface = session.query(NetworkInterface).filter_by(name=name).first()

    if not db_iface:
        return jsonify({"error": "Interface not found"}), 404

    # Get live interface data
    result = subprocess.run(
        ["../backend/target/debug/hardware_discovery"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return jsonify({"error": "Hardware discovery failed"}), 500

    interfaces = json.loads(result.stdout)
    live_iface = next((i for i in interfaces if i['name'] == name), None)

    if not live_iface:
        return jsonify({"error": "Interface not found in hardware"}), 404

    # Merge live data with DB configuration
    interface_data = {
        'id': db_iface.id,
        'name': db_iface.name,
        'label': db_iface.label,
        'is_wan': db_iface.is_wan,
        'dhcp_enabled': db_iface.dhcp_enabled,
        'static_ip': db_iface.static_ip,
        'static_netmask': db_iface.static_netmask,
        'static_gateway': db_iface.static_gateway,
        'dns_servers': db_iface.dns_servers,
        'mac': live_iface.get('mac'),
        'ips': live_iface.get('ips', []),
        'status': live_iface.get('status')
    }

    return jsonify(interface_data)

@interface_manager.route('/interfaces/<name>', methods=['PUT'])
def update_interface(name):
    """Update interface configuration"""
    session = Session()
    db_iface = session.query(NetworkInterface).filter_by(name=name).first()

    if not db_iface:
        return jsonify({"error": "Interface not found"}), 404

    try:
        data = request.json

        # Update database fields
        if 'label' in data:
            db_iface.label = data['label']

        if 'is_wan' in data:
            # If setting this interface as WAN, unset any other WAN interfaces
            if data['is_wan']:
                other_wans = session.query(NetworkInterface).filter(
                    NetworkInterface.is_wan == True,
                    NetworkInterface.name != name
                ).all()
                for other_wan in other_wans:
                    other_wan.is_wan = False

            db_iface.is_wan = data['is_wan']

        if 'dhcp_enabled' in data:
            db_iface.dhcp_enabled = data['dhcp_enabled']

        if 'static_ip' in data:
            db_iface.static_ip = data['static_ip']

        if 'static_netmask' in data:
            db_iface.static_netmask = data['static_netmask']

        if 'static_gateway' in data:
            db_iface.static_gateway = data['static_gateway']

        if 'dns_servers' in data:
            db_iface.dns_servers = data['dns_servers']

        session.commit()

        # Skip applying network config during the setup wizard
        # We'll apply everything at the end with apply-config

        return jsonify({"status": "success", "message": f"Interface {name} updated successfully"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

@interface_manager.route('/apply-config', methods=['POST'])
def apply_system_config():
    """Apply all network and firewall configurations"""
    session = Session()

    # Get all interfaces
    interfaces = session.query(NetworkInterface).all()

    if not interfaces:
        return jsonify({"error": "No interfaces configured"}), 500

    # Apply network configuration for each interface
    for iface in interfaces:
        success = apply_network_config(iface)
        if not success:
            return jsonify({"error": f"Failed to configure interface {iface.name}"}), 500

    # Set up firewall
    success = setup_firewall()
    if not success:
        return jsonify({"error": "Failed to configure firewall"}), 500

    return jsonify({
        "status": "success",
        "message": "System configuration applied successfully"
    })

def apply_network_config(interface):
    """Apply network configuration to the system"""
    # Get absolute path to the script
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/apply_network_config.sh'))
    
    # Build command to run the network configuration script without sudo
    # (assuming sudoers is configured properly)
    cmd = [
        script_path,
        interface.name,
        str(interface.is_wan),
        str(interface.dhcp_enabled),
        interface.static_ip or "192.168.1.1",  # Default for LAN
        interface.static_netmask or "255.255.255.0",
        interface.static_gateway or "",
        interface.dns_servers or "8.8.8.8,1.1.1.1"  # Default DNS servers
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Network configuration applied for {interface.name}:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error applying network configuration for {interface.name}:")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False


def setup_firewall():
    """Set up firewall with NAT for routing between interfaces"""
    session = Session()

    # Get WAN interface
    wan_iface = session.query(NetworkInterface).filter_by(is_wan=True).first()

    if not wan_iface:
        print("Error: No WAN interface configured")
        return False

    # Get LAN interfaces
    lan_ifaces = session.query(NetworkInterface).filter_by(is_wan=False).all()

    if not lan_ifaces:
        print("Error: No LAN interfaces configured")
        return False

    # Build comma-separated list of LAN interface names
    lan_names = ",".join([iface.name for iface in lan_ifaces])

    # Get absolute path to the script
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/setup_firewall.sh'))
    
    # Run firewall setup script
    cmd = [
        script_path,
        wan_iface.name,
        lan_names
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print("Firewall configured successfully:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error configuring firewall:")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False