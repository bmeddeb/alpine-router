// backend/src/main.rs
use pnet::datalink;
use serde::Serialize;

#[derive(Serialize)]
struct Interface {
    name: String,
    mac: Option<String>,
    ips: Vec<String>,
    status: String,
}

fn main() {
    let interfaces: Vec<Interface> = datalink::interfaces().into_iter().map(|iface| Interface {
        name: iface.name.clone(),
        mac: iface.mac.map(|m| m.to_string()),
        ips: iface.ips.iter().map(|ip| ip.to_string()).collect(),
        status: if iface.is_up() { "UP".into() } else { "DOWN".into() },
    }).collect();

    let json_output = serde_json::to_string_pretty(&interfaces).unwrap();
    println!("{}", json_output);
}