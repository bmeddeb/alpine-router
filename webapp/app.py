# app.py
from flask import Flask, jsonify, render_template
from dash_app import init_dash
from interface_manager import interface_manager
import subprocess
import json
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = 'sqlite:///alpine.db'

Base = declarative_base()

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

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def create_app():
    app = Flask(__name__)
    init_dash(app)

    # Register the interface_manager blueprint
    app.register_blueprint(interface_manager)

    @app.route('/')
    def root():
        return "Alpine Router Flask App"

    @app.route('/hardware')
    def hardware():
        session = Session()

        # Run Rust hardware discovery
        result = subprocess.run(
            ["../backend/target/debug/hardware_discovery"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({"error": "Hardware discovery failed"}), 500

        interfaces = json.loads(result.stdout)

        # Assign labels from DB or insert default if not existing
        for iface in interfaces:
            db_iface = session.query(NetworkInterface).filter_by(name=iface['name']).first()
            if not db_iface:
                # Insert interface into DB with default label
                db_iface = NetworkInterface(name=iface['name'])
                session.add(db_iface)
                session.commit()
            iface['label'] = db_iface.label  # Assign label to the output

        # Additional hardware information (CPU, RAM, Disk)
        hardware_info = get_additional_hardware_info()

        return jsonify({
            "interfaces": interfaces,
            "hardware_info": hardware_info
        })

    @app.route('/setup')
    def setup():
        return render_template('interface_setup.html')

    return app

def get_additional_hardware_info():
    import psutil
    return {
        "cpu": {
            "cores": psutil.cpu_count(),
            "usage_percent": psutil.cpu_percent(interval=1),
            "architecture": subprocess.getoutput("uname -m")
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "used": psutil.virtual_memory().used,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        }
    }

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)