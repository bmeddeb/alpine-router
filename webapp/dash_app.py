# webapp/dash_app.py
from dash import Dash, html, dcc, Input, Output, callback_context, State
import plotly.express as px
import plotly.graph_objects as go
import requests
import time
import pandas as pd

def init_dash(flask_app):
    dash_app = Dash(
        server=flask_app,
        routes_pathname_prefix='/dashboard/',
        external_stylesheets=[
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css',
            '/static/css/dashboard.css'
        ],
        suppress_callback_exceptions=True  # Important for multi-page apps
    )

    # Define the layout with navigation sidebar and content area
    dash_app.layout = html.Div([
        # Store the current page
        dcc.Store(id='current-page', data='overview'),
        
        # Store the latest data
        dcc.Store(id='hardware-data-store', data={}),
        
        # Automatic refresh interval (every 30 seconds)
        dcc.Interval(
            id='refresh-interval',
            interval=30 * 1000,  # in milliseconds
            n_intervals=0
        ),
        
        # Main layout with sidebar and content
        html.Div([
            # Sidebar
            html.Div([
                html.Div([
                    html.H2([html.I(className="fas fa-server mr-2"), " Alpine Router"]),
                ], className='sidebar-header'),
                
                html.Div([
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-tachometer-alt mr-2"),
                            "Overview"
                        ], id='nav-overview', className='nav-link active', n_clicks=0),
                        
                        html.Button([
                            html.I(className="fas fa-network-wired mr-2"),
                            "Network Interfaces"
                        ], id='nav-interfaces', className='nav-link', n_clicks=0),
                        
                        html.Button([
                            html.I(className="fas fa-shield-alt mr-2"),
                            "Firewall Rules"
                        ], id='nav-firewall', className='nav-link', n_clicks=0),
                        
                        html.Button([
                            html.I(className="fas fa-server mr-2"),
                            "DHCP Server"
                        ], id='nav-dhcp', className='nav-link', n_clicks=0),
                        
                        html.Button([
                            html.I(className="fas fa-globe mr-2"),
                            "DNS Settings"
                        ], id='nav-dns', className='nav-link', n_clicks=0),
                        
                        html.Button([
                            html.I(className="fas fa-chart-line mr-2"),
                            "Traffic Monitor"
                        ], id='nav-traffic', className='nav-link', n_clicks=0),
                        
                        html.Hr(),
                        
                        html.Button([
                            html.I(className="fas fa-cog mr-2"),
                            "Settings"
                        ], id='nav-settings', className='nav-link', n_clicks=0),
                        
                        html.A([
                            html.I(className="fas fa-sliders-h mr-2"),
                            "Setup Wizard"
                        ], href='/setup', className='nav-link')
                    ], className='nav-links')
                ], className='sidebar-content'),
                
                html.Div([
                    html.P("Alpine Router v0.1.0"),
                ], className='sidebar-footer')
            ], className='sidebar'),
            
            # Main content area
            html.Div([
                # Header with refresh button
                html.Div([
                    html.Div(id='page-title', className='page-title'),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-sync-alt mr-2"),
                            "Refresh"
                        ], id='refresh-btn', n_clicks=0, className='refresh-button'),
                        html.Div(id='last-update-time', className='last-update-time')
                    ], className='header-controls')
                ], className='content-header'),
                
                # Dynamic content area - changes based on navigation
                html.Div(id='page-content', className='content-body')
            ], className='main-content')
        ], className='dashboard-container')
    ])
    
    # Callback to update data store
    @dash_app.callback(
        [Output('hardware-data-store', 'data'),
         Output('last-update-time', 'children')],
        [Input('refresh-btn', 'n_clicks'),
         Input('refresh-interval', 'n_intervals')]
    )
    def update_data_store(n_clicks, n_intervals):
        current_time = time.strftime('%H:%M:%S')
        try:
            result = requests.get('http://localhost:5000/hardware')
            if result.status_code == 200:
                return result.json(), f'Last updated: {current_time}'
            else:
                return {}, f'Update failed at {current_time}'
        except Exception as e:
            return {}, f'Error: {str(e)}'
    
    # Simplified callback to switch pages
    @dash_app.callback(
        [Output('current-page', 'data'),
         Output('nav-overview', 'className'),
         Output('nav-interfaces', 'className'),
         Output('nav-firewall', 'className'),
         Output('nav-dhcp', 'className'),
         Output('nav-dns', 'className'),
         Output('nav-traffic', 'className'),
         Output('nav-settings', 'className')],
        [Input('nav-overview', 'n_clicks'),
         Input('nav-interfaces', 'n_clicks'),
         Input('nav-firewall', 'n_clicks'),
         Input('nav-dhcp', 'n_clicks'),
         Input('nav-dns', 'n_clicks'),
         Input('nav-traffic', 'n_clicks'),
         Input('nav-settings', 'n_clicks')],
        [State('current-page', 'data')]
    )
    def switch_page(overview_clicks, interfaces_clicks, firewall_clicks, 
                   dhcp_clicks, dns_clicks, traffic_clicks, settings_clicks, 
                   current_page):
        ctx = callback_context
        
        if not ctx.triggered:
            # No clicks yet
            return current_page, 'nav-link active', 'nav-link', 'nav-link', 'nav-link', 'nav-link', 'nav-link', 'nav-link'
            
        # Get the ID of the button that was clicked
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Set all nav classes to default
        nav_classes = {
            'nav-overview': 'nav-link',
            'nav-interfaces': 'nav-link',
            'nav-firewall': 'nav-link',
            'nav-dhcp': 'nav-link',
            'nav-dns': 'nav-link',
            'nav-traffic': 'nav-link',
            'nav-settings': 'nav-link'
        }
        
        # Set the active class for the clicked button
        nav_classes[button_id] = 'nav-link active'
        
        # Set the page based on which button was clicked
        page = button_id.replace('nav-', '')
        
        return (
            page,
            nav_classes['nav-overview'],
            nav_classes['nav-interfaces'],
            nav_classes['nav-firewall'],
            nav_classes['nav-dhcp'],
            nav_classes['nav-dns'],
            nav_classes['nav-traffic'],
            nav_classes['nav-settings']
        )
    
    # Callback to update page title
    @dash_app.callback(
        Output('page-title', 'children'),
        Input('current-page', 'data')
    )
    def update_page_title(current_page):
        titles = {
            'overview': 'System Overview',
            'interfaces': 'Network Interfaces',
            'firewall': 'Firewall Rules',
            'dhcp': 'DHCP Server',
            'dns': 'DNS Settings',
            'traffic': 'Traffic Monitor',
            'settings': 'System Settings'
        }
        return titles.get(current_page, 'Dashboard')
    
    # Callback to render the correct page content
    @dash_app.callback(
        Output('page-content', 'children'),
        [Input('current-page', 'data'),
         Input('hardware-data-store', 'data')]
    )
    def render_page_content(current_page, data):
        if not data:
            data = {}  # Provide a default empty dict to avoid errors
            
        if current_page == 'overview':
            return render_overview_page(data)
        elif current_page == 'interfaces':
            return render_interfaces_page(data)
        elif current_page == 'firewall':
            return render_firewall_page(data)
        elif current_page == 'dhcp':
            return render_dhcp_page(data)
        elif current_page == 'dns':
            return render_dns_page(data)
        elif current_page == 'traffic':
            return render_traffic_page(data)
        elif current_page == 'settings':
            return render_settings_page(data)
        else:
            return render_overview_page(data)  # Default to overview if page not found
    
    # ===== PAGE RENDERING FUNCTIONS =====
    
    def render_overview_page(data):
        # Simple overview page when no data is available
        if not data or not data.get('interfaces') or not data.get('hardware_info'):
            return html.Div([
                html.Div("No system data available. Please refresh the page.", className="alert alert-warning")
            ])
        
        interfaces = data.get('interfaces', [])
        hardware_info = data.get('hardware_info', {})
        
        # Count up/down interfaces
        up_interfaces = sum(1 for iface in interfaces if iface.get('status') == 'UP')
        total_interfaces = len(interfaces)
        
        # System cards
        system_cards = html.Div([
            # Network Status Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-network-wired"),
                ], className="card-icon"),
                html.Div([
                    html.H3("Network Status"),
                    html.Div([
                        html.Span(f"{up_interfaces}/{total_interfaces}"),
                        html.Span(" interfaces up")
                    ], className="card-value")
                ], className="card-content")
            ], className="status-card"),
            
            # CPU Status Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-microchip"),
                ], className="card-icon"),
                html.Div([
                    html.H3("CPU"),
                    html.Div(f"{hardware_info.get('cpu', {}).get('usage_percent', 0)}%", className="card-value"),
                    html.Div(f"Cores: {hardware_info.get('cpu', {}).get('cores', 'N/A')}", className="card-detail")
                ], className="card-content")
            ], className="status-card"),
            
            # Memory Status Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-memory"),
                ], className="card-icon"),
                html.Div([
                    html.H3("Memory"),
                    html.Div(f"{hardware_info.get('memory', {}).get('percent', 0)}%", className="card-value"),
                    html.Div([
                        f"Used: {hardware_info.get('memory', {}).get('used', 0) // (1024**2)} MB / ",
                        f"{hardware_info.get('memory', {}).get('total', 0) // (1024**2)} MB"
                    ], className="card-detail")
                ], className="card-content")
            ], className="status-card"),
            
            # Storage Status Card
            html.Div([
                html.Div([
                    html.I(className="fas fa-hdd"),
                ], className="card-icon"),
                html.Div([
                    html.H3("Storage"),
                    html.Div(f"{hardware_info.get('disk', {}).get('percent', 0)}%", className="card-value"),
                    html.Div([
                        f"Free: {hardware_info.get('disk', {}).get('free', 0) // (1024**3)} GB / ",
                        f"{hardware_info.get('disk', {}).get('total', 0) // (1024**3)} GB"
                    ], className="card-detail")
                ], className="card-content")
            ], className="status-card"),
        ], className="status-cards-grid")
        
        # Network interfaces
        network_interfaces = html.Div([
            html.Div([
                html.H3("Network Interfaces"),
                html.Div([
                    html.Div([
                        html.Div([
                            html.H4(iface['name'], className='interface-name'),
                            html.Span(iface['status'], className=f"status-badge {'status-up' if iface['status'] == 'UP' else 'status-down'}")
                        ], className='interface-header'),
                        html.Div([
                            html.Div(f"Type: {iface['label']}"),
                            html.Div(f"MAC: {iface['mac']}"),
                            html.Div(f"IPs: {', '.join(iface['ips']) if iface['ips'] else 'None'}")
                        ], className='interface-details')
                    ], className='interface-card') for iface in interfaces
                ], className='interfaces-grid')
            ], className="card interfaces-card")
        ])
        
        return html.Div([
            system_cards,
            network_interfaces
        ])

    def render_interfaces_page(data):
        """Render the network interfaces configuration page"""
        if not data or not data.get('interfaces'):
            return html.Div([
                html.Div("No interface data available. Please refresh the page.", className="alert alert-warning")
            ])

        interfaces = data.get('interfaces', [])

        # Organize interfaces by type
        wan_interfaces = [iface for iface in interfaces if iface.get('is_wan')]
        lan_interfaces = [iface for iface in interfaces if not iface.get('is_wan')]

        return html.Div([
            # Interface management header
            html.Div([
                html.Div([
                    html.H3("Network Interfaces"),
                    html.P("View and configure your network interfaces")
                ], className="module-header"),

                # WAN Interfaces section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-globe mr-2"),
                        "WAN Interfaces"
                    ], className="section-title"),
                    html.P("Internet-facing connections", className="section-description"),

                    html.Div([
                        html.Div([
                            # Interface header
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-network-wired mr-2"),
                                    iface['name']
                                ], className="interface-config-name"),
                                html.Div([
                                    html.Span(iface['status'], className=f"status-badge {'status-up' if iface['status'] == 'UP' else 'status-down'}")
                                ])
                            ], className="interface-config-header"),

                            # Interface details
                            html.Div([
                                html.Div([
                                    html.Div("MAC Address", className="detail-label"),
                                    html.Div(iface['mac'] or "N/A", className="detail-value")
                                ], className="detail-row"),

                                html.Div([
                                    html.Div("IP Configuration", className="detail-label"),
                                    html.Div("DHCP" if iface.get('dhcp_enabled', True) else "Static", className="detail-value")
                                ], className="detail-row"),

                                html.Div([
                                    html.Div("IP Address", className="detail-label"),
                                    html.Div(', '.join(iface['ips']) if iface['ips'] else "None assigned", className="detail-value")
                                ], className="detail-row"),

                                html.Div([
                                    html.Div("DNS Servers", className="detail-label"),
                                    html.Div(iface.get('dns_servers', "Not configured"), className="detail-value")
                                ], className="detail-row") if iface.get('is_wan') else None,
                            ], className="interface-config-details"),

                            # Interface actions
                            html.Div([
                                html.Button([
                                    html.I(className="fas fa-edit mr-2"),
                                    "Edit"
                                ], id=f"edit-interface-{iface['name']}", className="btn btn-primary mr-2"),

                                html.Button([
                                    html.I(className=f"fas {'fa-toggle-on' if iface['status'] == 'UP' else 'fa-toggle-off'} mr-2"),
                                    "Toggle"
                                ], id=f"toggle-interface-{iface['name']}", className="btn btn-secondary")
                            ], className="interface-config-actions")
                        ], className="interface-config-card") for iface in wan_interfaces
                    ], className="interface-config-grid"),

                    # Show message if no WAN interfaces
                    html.Div("No WAN interfaces configured. Please use the Setup Wizard to configure a WAN interface.",
                             className="alert alert-warning") if not wan_interfaces else None,
                ], className="interface-section"),

                # LAN Interfaces section
                html.Div([
                    html.H4([
                        html.I(className="fas fa-network-wired mr-2"),
                        "LAN Interfaces"
                    ], className="section-title"),
                    html.P("Local network connections", className="section-description"),

                    html.Div([
                        html.Div([
                            # Interface header
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-network-wired mr-2"),
                                    iface['name']
                                ], className="interface-config-name"),
                                html.Div([
                                    html.Span(iface['status'], className=f"status-badge {'status-up' if iface['status'] == 'UP' else 'status-down'}")
                                ])
                            ], className="interface-config-header"),

                            # Interface details
                            html.Div([
                                html.Div([
                                    html.Div("MAC Address", className="detail-label"),
                                    html.Div(iface['mac'] or "N/A", className="detail-value")
                                ], className="detail-row"),

                                html.Div([
                                    html.Div("IP Address", className="detail-label"),
                                    html.Div(', '.join(iface['ips']) if iface['ips'] else "None assigned", className="detail-value")
                                ], className="detail-row"),

                                html.Div([
                                    html.Div("DHCP Server", className="detail-label"),
                                    html.Div("Enabled" if iface.get('dhcp_enabled', True) else "Disabled", className="detail-value")
                                ], className="detail-row"),
                            ], className="interface-config-details"),

                            # Interface actions
                            html.Div([
                                html.Button([
                                    html.I(className="fas fa-edit mr-2"),
                                    "Edit"
                                ], id=f"edit-interface-{iface['name']}", className="btn btn-primary mr-2"),

                                html.Button([
                                    html.I(className=f"fas {'fa-toggle-on' if iface['status'] == 'UP' else 'fa-toggle-off'} mr-2"),
                                    "Toggle"
                                ], id=f"toggle-interface-{iface['name']}", className="btn btn-secondary")
                            ], className="interface-config-actions")
                        ], className="interface-config-card") for iface in lan_interfaces
                    ], className="interface-config-grid"),

                    # Show message if no LAN interfaces
                    html.Div("No LAN interfaces configured. Please use the Setup Wizard to configure at least one LAN interface.",
                             className="alert alert-warning") if not lan_interfaces else None,
                ], className="interface-section"),
            ], className="card")
        ])

    def render_dhcp_page(data):
        """Render the DHCP server configuration page"""
        if not data or not data.get('interfaces'):
            return html.Div([
                html.Div("No interface data available. Please refresh the page.", className="alert alert-warning")
            ])

        interfaces = data.get('interfaces', [])

        # Get LAN interfaces (only these can run DHCP server)
        lan_interfaces = [iface for iface in interfaces if not iface.get('is_wan')]

        # Sample DHCP configuration (would come from API/database in real implementation)
        dhcp_config = {
            'enabled': True,
            'start_ip': '192.168.1.100',
            'end_ip': '192.168.1.200',
            'lease_time': 24,  # hours
            'domain': 'lan.local',
            'static_leases': [
                {'mac': '00:11:22:33:44:55', 'ip': '192.168.1.10', 'hostname': 'desktop-pc'},
                {'mac': 'aa:bb:cc:dd:ee:ff', 'ip': '192.168.1.20', 'hostname': 'printer'}
            ]
        }

        return html.Div([
            # DHCP Server settings card
            html.Div([
                html.Div([
                    html.H3("DHCP Server Settings"),
                    html.P("Configure automatic IP address assignment for your network")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Div([
                            html.Label("DHCP Server Status", htmlFor="dhcp-status"),
                            dcc.Dropdown(
                                id="dhcp-status",
                                options=[
                                    {'label': 'Enabled', 'value': 'enabled'},
                                    {'label': 'Disabled', 'value': 'disabled'}
                                ],
                                value='enabled' if dhcp_config['enabled'] else 'disabled',
                                clearable=False,
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),

                        html.Div([
                            html.Label("Interface", htmlFor="dhcp-interface"),
                            dcc.Dropdown(
                                id="dhcp-interface",
                                options=[
                                    {'label': iface['name'], 'value': iface['name']} for iface in lan_interfaces
                                ],
                                value=lan_interfaces[0]['name'] if lan_interfaces else None,
                                placeholder="Select LAN interface",
                                clearable=False,
                                className="form-control",
                                disabled=len(lan_interfaces) == 0
                            )
                        ], className="form-group col-md-6"),
                    ], className="form-row"),

                    html.Div([
                        html.Div([
                            html.Label("IP Range Start", htmlFor="dhcp-start"),
                            dcc.Input(
                                id="dhcp-start",
                                type="text",
                                value=dhcp_config['start_ip'],
                                placeholder="e.g., 192.168.1.100",
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),

                        html.Div([
                            html.Label("IP Range End", htmlFor="dhcp-end"),
                            dcc.Input(
                                id="dhcp-end",
                                type="text",
                                value=dhcp_config['end_ip'],
                                placeholder="e.g., 192.168.1.200",
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),
                    ], className="form-row"),

                    html.Div([
                        html.Div([
                            html.Label("Lease Time (hours)", htmlFor="dhcp-lease"),
                            dcc.Input(
                                id="dhcp-lease",
                                type="number",
                                value=dhcp_config['lease_time'],
                                min=1,
                                max=168,  # 1 week max
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),

                        html.Div([
                            html.Label("Domain Name", htmlFor="dhcp-domain"),
                            dcc.Input(
                                id="dhcp-domain",
                                type="text",
                                value=dhcp_config['domain'],
                                placeholder="e.g., lan.local",
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),
                    ], className="form-row"),

                    html.Div([
                        html.Button([
                            html.I(className="fas fa-save mr-2"),
                            "Save Settings"
                        ], id="save-dhcp-settings", className="btn btn-primary")
                    ], className="form-actions"),
                ], className="dhcp-settings-form"),
            ], className="card"),

            # Static DHCP leases card
            html.Div([
                html.Div([
                    html.H3("Static DHCP Leases"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Static Lease"
                        ], id="add-dhcp-lease", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Hostname"),
                                    html.Th("MAC Address"),
                                    html.Th("IP Address"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(lease['hostname']),
                                    html.Td(lease['mac']),
                                    html.Td(lease['ip']),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id=f"edit-lease-{i}", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id=f"delete-lease-{i}", className="btn btn-sm btn-danger")
                                    ])
                                ]) for i, lease in enumerate(dhcp_config['static_leases'])
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),

            # DHCP Leases card (active leases)
            html.Div([
                html.Div([
                    html.H3("Active DHCP Leases"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-sync-alt mr-2"),
                            "Refresh Leases"
                        ], id="refresh-dhcp-leases", className="btn btn-secondary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Hostname"),
                                    html.Th("MAC Address"),
                                    html.Th("IP Address"),
                                    html.Th("Expires")
                                ])
                            ]),
                            html.Tbody([
                                # Example active leases - would be populated from backend
                                html.Tr([
                                    html.Td("laptop-1"),
                                    html.Td("11:22:33:44:55:66"),
                                    html.Td("192.168.1.101"),
                                    html.Td("23 hours")
                                ]),
                                html.Tr([
                                    html.Td("smartphone"),
                                    html.Td("aa:bb:cc:11:22:33"),
                                    html.Td("192.168.1.102"),
                                    html.Td("22 hours")
                                ]),
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),
        ])

    def render_firewall_page(data):
        """Render the firewall rules management page"""

        # Sample firewall rules (hardcoded for now)
        firewall_rules = [
            {
                'id': 1,
                'name': 'Allow SSH',
                'src': 'WAN',
                'dst': 'LAN',
                'protocol': 'TCP',
                'port': '22',
                'action': 'ACCEPT',
                'enabled': True
            },
            {
                'id': 2,
                'name': 'Block Telnet',
                'src': 'ANY',
                'dst': 'LAN',
                'protocol': 'TCP',
                'port': '23',
                'action': 'DROP',
                'enabled': True
            },
            {
                'id': 3,
                'name': 'Allow Web Access',
                'src': 'LAN',
                'dst': 'ANY',
                'protocol': 'TCP',
                'port': '80,443',
                'action': 'ACCEPT',
                'enabled': True
            },
            {
                'id': 4,
                'name': 'Allow DNS',
                'src': 'LAN',
                'dst': 'ANY',
                'protocol': 'UDP',
                'port': '53',
                'action': 'ACCEPT',
                'enabled': True
            }
        ]

        # Firewall zones (hardcoded for now)
        firewall_zones = [
            {'id': 'WAN', 'name': 'WAN (Internet)', 'default_policy': 'DROP'},
            {'id': 'LAN', 'name': 'LAN (Local Network)', 'default_policy': 'ACCEPT'},
            {'id': 'DMZ', 'name': 'DMZ', 'default_policy': 'DROP'}
        ]

        return html.Div([
            # Firewall status card
            html.Div([
                html.Div([
                    html.H3("Firewall Status"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-power-off mr-2"),
                            "Toggle Firewall"
                        ], id="toggle-firewall-btn", className="btn btn-warning")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-shield-alt"),
                        ], className="status-icon"),
                        html.Div([
                            html.Div("Active", className="status-label status-active"),
                            html.Div("The firewall is currently enforcing all rules", className="status-description")
                        ], className="status-details")
                    ], className="status-indicator-card")
                ], className="status-section")
            ], className="card"),

            # Firewall zones card
            html.Div([
                html.Div([
                    html.H3("Network Zones"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Zone"
                        ], id="add-zone-btn", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Zone"),
                                    html.Th("Description"),
                                    html.Th("Default Policy"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(zone['id']),
                                    html.Td(zone['name']),
                                    html.Td([
                                        html.Span(zone['default_policy'],
                                                  className=f"policy-badge {'accept' if zone['default_policy'] == 'ACCEPT' else 'drop'}")
                                    ]),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id=f"edit-zone-{zone['id']}", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id=f"delete-zone-{zone['id']}",
                                            className="btn btn-sm btn-danger",
                                            disabled=zone['id'] in ['WAN', 'LAN'])  # Can't delete default zones
                                    ])
                                ]) for zone in firewall_zones
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),

            # Firewall rules card
            html.Div([
                html.Div([
                    html.H3("Firewall Rules"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Rule"
                        ], id="add-rule-btn", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Name"),
                                    html.Th("Source"),
                                    html.Th("Destination"),
                                    html.Th("Protocol"),
                                    html.Th("Port"),
                                    html.Th("Action"),
                                    html.Th("Status"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(rule['name']),
                                    html.Td(rule['src']),
                                    html.Td(rule['dst']),
                                    html.Td(rule['protocol']),
                                    html.Td(rule['port']),
                                    html.Td([
                                        html.Span(rule['action'],
                                                  className=f"policy-badge {'accept' if rule['action'] == 'ACCEPT' else 'drop'}")
                                    ]),
                                    html.Td([
                                        html.Span("Enabled" if rule['enabled'] else "Disabled",
                                                  className=f"status-badge {'status-up' if rule['enabled'] else 'status-down'}")
                                    ]),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id=f"edit-rule-{rule['id']}", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-toggle-on" if rule['enabled'] else "fa-toggle-off")
                                        ], id=f"toggle-rule-{rule['id']}", className="btn btn-sm btn-secondary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id=f"delete-rule-{rule['id']}", className="btn btn-sm btn-danger")
                                    ])
                                ]) for rule in firewall_rules
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),

            # Port forwarding card
            html.Div([
                html.Div([
                    html.H3("Port Forwarding"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Port Forward"
                        ], id="add-port-forward-btn", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    # Example port forwarding rules
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Name"),
                                    html.Th("External Port"),
                                    html.Th("Internal IP"),
                                    html.Th("Internal Port"),
                                    html.Th("Protocol"),
                                    html.Th("Status"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td("Web Server"),
                                    html.Td("80"),
                                    html.Td("192.168.1.10"),
                                    html.Td("80"),
                                    html.Td("TCP"),
                                    html.Td([
                                        html.Span("Enabled", className="status-badge status-up")
                                    ]),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id="edit-port-forward-1", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-toggle-on")
                                        ], id="toggle-port-forward-1", className="btn btn-sm btn-secondary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id="delete-port-forward-1", className="btn btn-sm btn-danger")
                                    ])
                                ]),
                                html.Tr([
                                    html.Td("SSH Access"),
                                    html.Td("2222"),
                                    html.Td("192.168.1.10"),
                                    html.Td("22"),
                                    html.Td("TCP"),
                                    html.Td([
                                        html.Span("Enabled", className="status-badge status-up")
                                    ]),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id="edit-port-forward-2", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-toggle-on")
                                        ], id="toggle-port-forward-2", className="btn btn-sm btn-secondary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id="delete-port-forward-2", className="btn btn-sm btn-danger")
                                    ])
                                ])
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),
        ])


    def render_dns_page(data):
        """Render the DNS settings page"""

        # Sample DNS settings (hardcoded for now)
        dns_settings = {
            'primary_dns': '8.8.8.8',
            'secondary_dns': '1.1.1.1',
            'local_domain': 'lan.local',
            'enable_dns_forwarding': True,
            'enable_dnssec': True,
            'blocking_enabled': True,
            'blocked_domains': [
                'ads.example.com',
                'malware.example.com',
                'tracker.example.com'
            ],
            'custom_entries': [
                {'hostname': 'router', 'ip': '192.168.1.1'},
                {'hostname': 'nas', 'ip': '192.168.1.10'},
                {'hostname': 'printer', 'ip': '192.168.1.20'}
            ]
        }

        return html.Div([
            # DNS server settings card
            html.Div([
                html.Div([
                    html.H3("DNS Server Settings"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-save mr-2"),
                            "Save Changes"
                        ], id="save-dns-settings", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Div([
                            html.Label("Primary DNS Server", htmlFor="primary-dns"),
                            dcc.Input(
                                id="primary-dns",
                                type="text",
                                value=dns_settings['primary_dns'],
                                placeholder="e.g., 8.8.8.8",
                                className="form-control"
                            )
                        ], className="form-group col-md-6"),

                        html.Div([
                            html.Label("Secondary DNS Server", htmlFor="secondary-dns"),
                            dcc.Input(
                                id="secondary-dns",
                                type="text",
                                value=dns_settings['secondary_dns'],
                                placeholder="e.g., 1.1.1.1",
                                className="form-control"
                            )
                        ], className="form-group col-md-6")
                    ], className="form-row"),

                    html.Div([
                        html.Div([
                            html.Label("Local Domain", htmlFor="local-domain"),
                            dcc.Input(
                                id="local-domain",
                                type="text",
                                value=dns_settings['local_domain'],
                                placeholder="e.g., lan.local",
                                className="form-control"
                            )
                        ], className="form-group col-md-12")
                    ], className="form-row"),

                    html.Div([
                        html.Div([
                            html.H4("DNS Features"),
                            dcc.Checklist(
                                id="dns-features",
                                options=[
                                    {'label': 'Enable DNS Forwarding', 'value': 'FORWARDING'},
                                    {'label': 'Enable DNSSEC', 'value': 'DNSSEC'},
                                    {'label': 'Enable Domain Blocking', 'value': 'BLOCKING'}
                                ],
                                value=[
                                    'FORWARDING' if dns_settings['enable_dns_forwarding'] else '',
                                    'DNSSEC' if dns_settings['enable_dnssec'] else '',
                                    'BLOCKING' if dns_settings['blocking_enabled'] else ''
                                ],
                                labelStyle={'display': 'block', 'marginBottom': '10px'}
                            )
                        ], className="form-group col-md-12")
                    ], className="form-row")
                ], className="dns-settings-form")
            ], className="card"),

            # DNS domain blocking card
            html.Div([
                html.Div([
                    html.H3("Domain Blocking"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Domain"
                        ], id="add-blocked-domain", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Domain"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(domain),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id=f"delete-domain-{i}", className="btn btn-sm btn-danger")
                                    ])
                                ]) for i, domain in enumerate(dns_settings['blocked_domains'])
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card"),

            # DNS local entries card
            html.Div([
                html.Div([
                    html.H3("Local DNS Entries"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-plus mr-2"),
                            "Add Entry"
                        ], id="add-dns-entry", className="btn btn-primary")
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Hostname"),
                                    html.Th("IP Address"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(entry['hostname']),
                                    html.Td(entry['ip']),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-edit")
                                        ], id=f"edit-dns-{i}", className="btn btn-sm btn-primary mr-2"),
                                        html.Button([
                                            html.I(className="fas fa-trash")
                                        ], id=f"delete-dns-{i}", className="btn btn-sm btn-danger")
                                    ])
                                ]) for i, entry in enumerate(dns_settings['custom_entries'])
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card")
        ])

    def render_traffic_page(data):
        """Render the traffic monitor page"""

        # Sample traffic data (hardcoded for now)
        traffic_data = {
            'interfaces': [
                {'name': 'eth0', 'rx_bytes': 1024000, 'tx_bytes': 512000, 'rx_packets': 1500, 'tx_packets': 1200},
                {'name': 'eth1', 'rx_bytes': 2048000, 'tx_bytes': 1024000, 'rx_packets': 3000, 'tx_packets': 2500}
            ],
            'top_connections': [
                {'src_ip': '192.168.1.10', 'dst_ip': '203.0.113.1', 'protocol': 'TCP', 'dst_port': 443, 'bytes': 1024000},
                {'src_ip': '192.168.1.15', 'dst_ip': '198.51.100.1', 'protocol': 'UDP', 'dst_port': 53, 'bytes': 51200},
                {'src_ip': '192.168.1.20', 'dst_ip': '198.51.100.5', 'protocol': 'TCP', 'dst_port': 80, 'bytes': 512000}
            ]
        }

        # Create a traffic graph
        traffic_graph = dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        name='Received (RX)',
                        x=[iface['name'] for iface in traffic_data['interfaces']],
                        y=[iface['rx_bytes'] / (1024*1024) for iface in traffic_data['interfaces']],
                        marker_color='#3498db'
                    ),
                    go.Bar(
                        name='Transmitted (TX)',
                        x=[iface['name'] for iface in traffic_data['interfaces']],
                        y=[iface['tx_bytes'] / (1024*1024) for iface in traffic_data['interfaces']],
                        marker_color='#2ecc71'
                    )
                ],
                layout=go.Layout(
                    title='Network Traffic by Interface (MB)',
                    barmode='group',
                    margin=dict(l=40, r=40, t=80, b=40)
                )
            ),
            config={'displayModeBar': False}
        )

        # Create a packets graph
        packets_graph = dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        name='Received (RX)',
                        x=[iface['name'] for iface in traffic_data['interfaces']],
                        y=[iface['rx_packets'] for iface in traffic_data['interfaces']],
                        marker_color='#3498db'
                    ),
                    go.Bar(
                        name='Transmitted (TX)',
                        x=[iface['name'] for iface in traffic_data['interfaces']],
                        y=[iface['tx_packets'] for iface in traffic_data['interfaces']],
                        marker_color='#2ecc71'
                    )
                ],
                layout=go.Layout(
                    title='Network Packets by Interface',
                    barmode='group',
                    margin=dict(l=40, r=40, t=80, b=40)
                )
            ),
            config={'displayModeBar': False}
        )

        return html.Div([
            # Traffic overview card
            html.Div([
                html.Div([
                    html.H3("Network Traffic"),
                    html.Div([
                        html.Button([
                            html.I(className="fas fa-sync-alt mr-2"),
                            "Refresh"
                        ], id="refresh-traffic", className="btn btn-secondary"),
                        dcc.Dropdown(
                            id="traffic-timeframe",
                            options=[
                                {'label': 'Last Hour', 'value': '1h'},
                                {'label': 'Last 6 Hours', 'value': '6h'},
                                {'label': 'Last 24 Hours', 'value': '24h'},
                                {'label': 'Last Week', 'value': '1w'}
                            ],
                            value='1h',
                            clearable=False,
                            style={'width': '150px', 'marginLeft': '10px'}
                        )
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        traffic_graph
                    ], className="chart-container"),

                    html.Div([
                        packets_graph
                    ], className="chart-container mt-4")
                ], className="module-content")
            ], className="card"),

            # Top connections card
            html.Div([
                html.Div([
                    html.H3("Top Connections"),
                    html.Div([
                        dcc.Dropdown(
                            id="top-connections-filter",
                            options=[
                                {'label': 'All', 'value': 'all'},
                                {'label': 'TCP Only', 'value': 'tcp'},
                                {'label': 'UDP Only', 'value': 'udp'}
                            ],
                            value='all',
                            clearable=False,
                            style={'width': '150px'}
                        )
                    ], className="module-actions")
                ], className="module-header"),

                html.Div([
                    html.Div([
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Source IP"),
                                    html.Th("Destination IP"),
                                    html.Th("Protocol"),
                                    html.Th("Port"),
                                    html.Th("Data"),
                                    html.Th("Actions")
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(conn['src_ip']),
                                    html.Td(conn['dst_ip']),
                                    html.Td(conn['protocol']),
                                    html.Td(conn['dst_port']),
                                    html.Td(f"{conn['bytes'] / 1024:.2f} KB"),
                                    html.Td([
                                        html.Button([
                                            html.I(className="fas fa-ban")
                                        ], id=f"block-conn-{i}", className="btn btn-sm btn-danger", title="Block this connection")
                                    ])
                                ]) for i, conn in enumerate(traffic_data['top_connections'])
                            ])
                        ], className="data-table")
                    ], className="table-container")
                ], className="module-content")
            ], className="card")
        ])

    def render_settings_page(data):
        return html.Div([
            html.Div("System Settings page coming soon...", className="card")
        ])
    
    return dash_app