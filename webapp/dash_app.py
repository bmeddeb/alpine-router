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
    
    # Placeholder functions for other pages
    def render_interfaces_page(data):
        return html.Div([
            html.Div("Network Interfaces configuration page coming soon...", className="card")
        ])
    
    def render_firewall_page(data):
        return html.Div([
            html.Div("Firewall Rules configuration page coming soon...", className="card")
        ])
    
    def render_dhcp_page(data):
        return html.Div([
            html.Div("DHCP Server configuration page coming soon...", className="card")
        ])
    
    def render_dns_page(data):
        return html.Div([
            html.Div("DNS Settings configuration page coming soon...", className="card")
        ])
    
    def render_traffic_page(data):
        return html.Div([
            html.Div("Traffic Monitor page coming soon...", className="card")
        ])
    
    def render_settings_page(data):
        return html.Div([
            html.Div("System Settings page coming soon...", className="card")
        ])
    
    return dash_app