import os
import json

CONFIG_FILE = r"Chat Logger\config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Config introuvable : {CONFIG_FILE}")

def generate_hub(config):
    output_dir = config.get("OUTPUT_DIR", "")
    if not output_dir or not os.path.isdir(output_dir):
        raise FileNotFoundError("❌ OUTPUT_DIR invalide dans config.json")

    index_file = os.path.join("Chat Logger", "logs_index.html")

    log_files = [f for f in os.listdir(output_dir) if f.endswith(".html") and f.startswith("log_")]
    log_files.sort(reverse=True)

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Hub des Logs Minecraft</title>
<style>
body {{
    background-color:#1e1e1e;
    color:#f0f0f0;
    font-family:Consolas, monospace;
    margin:0; padding:20px;
}}
h1 {{
    text-align:center;
    margin-bottom:10px;
}}
#log-count {{
    text-align:center;
    color:#aaa;
    margin-bottom:20px;
}}
.log-link {{
    display:block;
    background:#2b2b2b;
    margin:10px auto;
    padding:12px 18px;
    border-radius:10px;
    width:80%;
    text-decoration:none;
    color:#f0f0f0;
    transition: all 0.2s ease;
    box-shadow:0 0 6px rgba(0,0,0,0.5);
}}
.log-link:hover {{
    background:#3a3a3a;
    transform: translateY(-3px);
    box-shadow:0 10px 20px rgba(0,0,0,0.6);
}}
#scrollTopBtn {{
    opacity: 0;
    pointer-events: none;
    position: fixed;
    bottom: 30px;
    right: 15px;
    z-index: 100;
    border: none;
    outline: none;
    background-color: #3a3a3a;
    color: white;
    cursor: pointer;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    font-size: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
    transition: opacity 0.4s ease, transform 0.2s ease;
}}
#scrollTopBtn.show {{
    opacity: 1;
    pointer-events: auto;
}}
#scrollTopBtn:hover {{
    background-color: #5a5a5a;
    transform: translateY(-3px);
}}
</style>
</head>
<body>
<h1>📜 Hub des Logs Minecraft</h1>
<div id="log-count">Chargement du nombre de logs...</div>
<button onclick="topFunction()" id="scrollTopBtn" title="Remonter en haut">⬆</button>
<a class="log-link" href="logs.html">🔍 View All Logs and Search</a>
""")

        for log in log_files:
            f.write(f'<a class="log-link log-entry" href="Logs/{log}">🔗 {log}</a>\n')

        f.write("""
<script>
window.addEventListener("DOMContentLoaded", () => {
    const logs = document.querySelectorAll(".log-entry");
    const countDiv = document.getElementById("log-count");
    countDiv.textContent = logs.length > 0 
        ? `📂 ${logs.length} fichiers de logs disponibles` 
        : "❌ Aucun log trouvé.";
});
let mybutton = document.getElementById("scrollTopBtn");
window.addEventListener("scroll", () => {
  if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
    mybutton.classList.add("show");
  } else {
    mybutton.classList.remove("show");
  }
});
function topFunction() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>
</body></html>
""")

    print(f"✅ Hub généré : {index_file}")

if __name__ == "__main__":
    config = load_config()
    generate_hub(config)
