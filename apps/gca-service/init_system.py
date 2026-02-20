import torch
import os
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.decomposition import PCA
import numpy as np

# Load Config
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path) as f:
    CFG = yaml.safe_load(f)

def map_brain():
    model_id = CFG.get('system', {}).get('model_id')
    trust_remote_code = CFG.get('system', {}).get('trust_remote_code', False)

    print(f"[🗺️] Mapping Latent Space for {model_id}...")

    # 1. Load Model
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=trust_remote_code)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=getattr(torch, CFG['system'].get('dtype', 'float32')),
        trust_remote_code=trust_remote_code
    )

    # 2. Calibration Prompts (The Compass)
    prompts = [
        "The fundamental laws of physics are",
        "SELECT * FROM users WHERE id =",
        "To execute a python script, run",
        "I love you, you are my best friend",
        "The quarterly financial report shows",
        "sudo rm -rf / is a dangerous command",
        "Write a haiku about the moon",
        "JSON format is defined as",
        "The logic of the argument is flawed because",
        "import os; os.system('ls')"
    ] * 10 # Repeat to get variance

    # 3. Harvest States
    states = []
    layer_idx = CFG['geometry']['layer_idx']

    def hook(module, input, output):
        # Mean pool the hidden states
        # output is tuple (hidden_states,)
        if isinstance(output, tuple):
            hidden = output[0]
        else:
            hidden = output

        states.append(torch.mean(hidden, dim=1).detach().cpu().float())

    # Attach hook
    # Adjust for different model architectures if needed (this works for many HF models)
    if hasattr(model, "model"):
        if hasattr(model.model, "layers"):
            layer = model.model.layers[layer_idx]
        elif hasattr(model.model, "decoder"): # For some encoder-decoder
             layer = model.model.decoder.layers[layer_idx]
        else:
             # Fallback or error
             print("Warning: Could not find layer structure, using first layer available or skipping")
             layer = list(model.modules())[layer_idx] # Risky but fallback
    elif hasattr(model, "transformer"):
        layer = model.transformer.h[layer_idx]
    else:
        print("Error: Unknown model architecture")
        return

    handle = layer.register_forward_hook(hook)

    # Run Inference
    print("[1/2] Harvesting activations...")
    for p in prompts:
        inputs = tokenizer(p, return_tensors="pt")
        with torch.no_grad():
            model(**inputs)

    handle.remove()

    # 4. Compute Basis (SVD/PCA)
    print("[2/2] Calculating Universal Basis...")
    if not states:
        print("Error: No states captured.")
        return

    matrix = torch.cat(states, dim=0).numpy()
    pca = PCA(n_components=CFG['geometry']['basis_size'])
    pca.fit(matrix)

    basis = torch.tensor(pca.components_, dtype=torch.float32)

    # 5. Save
    assets_dir = os.environ.get('GCA_ASSETS_DIR', CFG['geometry']['assets_dir'])
    os.makedirs(assets_dir, exist_ok=True)
    save_path = os.path.join(assets_dir, "universal_basis.pt")
    torch.save(basis, save_path)
    print(f"[✅] Map Saved to {save_path}")

if __name__ == "__main__":
    map_brain()
