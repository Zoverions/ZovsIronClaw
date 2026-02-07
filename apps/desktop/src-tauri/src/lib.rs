use tauri::Manager;
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::CommandEvent;
use std::path::PathBuf;
use tokio::fs;
use tokio::io::AsyncWriteExt;

// Check if model file exists
#[tauri::command]
fn check_model_exists(filename: &str) -> bool {
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
            // Using "download-progress" channel
            window.emit("download-progress", progress).unwrap_or(());
        }
    }

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
        .invoke_handler(tauri::generate_handler![check_model_exists, download_model])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
