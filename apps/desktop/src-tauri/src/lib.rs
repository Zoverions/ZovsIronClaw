use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use std::path::PathBuf;
use tokio::fs;
use tokio::io::AsyncWriteExt;

// Sanitize filename to prevent path traversal
fn is_safe_filename(filename: &str) -> bool {
    // Only allow alphanumeric, dashes, underscores, and dots
    filename.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_' || c == '.') &&
    !filename.contains("..") &&
    !filename.contains("/") &&
    !filename.contains("\\")
}

// Check if model file exists
#[tauri::command]
fn check_model_exists(filename: &str) -> bool {
    if !is_safe_filename(filename) {
        return false;
    }
    if let Some(mut path) = dirs::data_dir() {
        path.push("ZovsIronClaw");
        path.push("models");
        path.push(filename);
        return path.exists();
    }
    false
}

// Download model file
#[tauri::command]
async fn download_model(url: &str, filename: &str, window: tauri::Window) -> Result<(), String> {
    if !is_safe_filename(filename) {
        return Err("Invalid filename".to_string());
    }

    let mut path = dirs::data_dir().ok_or("Could not find data directory")?;
    path.push("ZovsIronClaw");
    path.push("models");

    // Create directory if it doesn't exist
    if !path.exists() {
        fs::create_dir_all(&path).await.map_err(|e| e.to_string())?;
    }

    path.push(filename);

    let client = reqwest::Client::new();
    let mut response = client.get(url).send().await.map_err(|e| e.to_string())?;

    if !response.status().is_success() {
        return Err(format!("Download failed: {}", response.status()));
    }

    let total_size = response.content_length().unwrap_or(0);
    let mut downloaded: u64 = 0;

    let mut file = fs::File::create(&path).await.map_err(|e| e.to_string())?;

    // Stream the body chunk by chunk
    while let Some(chunk) = response.chunk().await.map_err(|e| e.to_string())? {
        file.write_all(&chunk).await.map_err(|e| e.to_string())?;
        downloaded += chunk.len() as u64;

        if total_size > 0 {
            let progress = (downloaded as f64 / total_size as f64) * 100.0;
            // Emit progress event to frontend
            window.emit("download-progress", progress).unwrap_or(());
        }
    }

    Ok(())
}

// Save Soul Configuration
#[tauri::command]
async fn save_soul_config(soul_name: &str) -> Result<(), String> {
    if !is_safe_filename(soul_name) {
        return Err("Invalid soul name".to_string());
    }

    let mut path = dirs::data_dir().ok_or("Could not find data directory")?;
    path.push("ZovsIronClaw");

    if !path.exists() {
        fs::create_dir_all(&path).await.map_err(|e| e.to_string())?;
    }

    path.push("config.json");

    // Load existing config if possible
    let mut config = serde_json::Map::new();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path).await {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&content) {
                if let Some(obj) = json.as_object() {
                    config = obj.clone();
                }
            }
        }
    }

    // Update soul
    config.insert("active_soul".to_string(), serde_json::Value::String(soul_name.to_string()));

    // Write back
    let json_str = serde_json::to_string_pretty(&config).map_err(|e| e.to_string())?;
    fs::write(&path, json_str).await.map_err(|e| e.to_string())?;

    Ok(())
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let shell = app.shell();
            let sidecar_command = shell.sidecar("gca-brain").expect("failed to setup sidecar");

            let (mut rx, _child) = sidecar_command
                .spawn()
                .expect("Failed to spawn sidecar");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                             let line_str = String::from_utf8_lossy(&line);
                             println!("[BRAIN]: {}", line_str);
                        }
                        CommandEvent::Stderr(line) => {
                             let line_str = String::from_utf8_lossy(&line);
                             eprintln!("[BRAIN-ERR]: {}", line_str);
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            check_model_exists,
            download_model,
            save_soul_config
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
