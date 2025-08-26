import os
import time
import datetime
import re
import json
import requests

CONFIG_FILE = r"Chat Logger\config.json"

categories = {
    "Players": {
        "messages": [],
        "exclude_filters": [", turtlesmile5110", "[replay mod]"],
        "include_filters": [],
        "exclusive": False
    },
    "Craftok": {
        "messages": [],
        "exclude_filters": ["informations sur"],
        "include_filters": [
            "vous venez d'activer le mode","vous venez de désactiver le mode","vient de se connecter",
            "vient de se déconnecter","vous venez désactiver le mode","vous êtes déjà en vanish",
            "vous êtes encore en vanish","téléportation à :","ce joueur n'existe pas","teleportation à :",
            "ac info]","tp]","info]","casier]","début de la traque de","mode traque désactivé","[pv]",
            "début de la procédure de génération du nick...","vous êtes à présent nick","vous ne serez dorénavant plus nick.",
            "pseudo: ","le changement de pseudo et de skin sera effectif lorsque vous vous rendrez sur un autre serveur",
            "pour retirer le nick refaîtes /nick.","vous avez rejoint la file d'attente pour","vous venez de désactiver les alerts",
            "vous venez d'activer les alerts","vous avez commencé le parkour","vous avez recommencé le parkour ! votre temps a été remis à 0 !",
            "vous avez été téléporté à votre dernier checkpoint.","vous avez été téléporté au début",
            "you cannot mount an entity while in a parkour","vous avez quitté le parkour et votre progression à été remise à zéro.",
            "vous ne pouvez pas voler pendant le parkour","vous venez d'activer le double jump","merci d'enlever votre double jump !",
            "vous venez désactiver le double jump","vous avez fait apparaître","vous avez fait disparaître","vous avez activé",
            "vous avez desactivé","dorénavant, tout le monde peut vous inviter dans sa partie","dorénavant, seulement vos amis peuvent vous inviter dans leur partie",
            "vous ne recevrez plus de message quand un ami se connecte","vous recevrez de nouveau un message quand un ami se connecte",
            "craftok - grade perso","vous ne possédez pas le grade perso","vous avez déjà ce grade !","connexion en cours au serveur",
            "téléportation de : ","vous avez été réduit au silence pour","vous pourrez à nouveau parler dans"
        ],
        "exclusive": True
    },
    "AntiCheat": {
        "messages": [],
        "exclude_filters": [
            "liste d'amis","utilisation:","commandes de parties:","commandes d'amis:",
            "vous ne pouvez pas vous envoyer de message","vous ne pouvez pas vous ajouter en ami","vous ne pouvez pas vous inviter dans votre propre partie"
        ],
        "include_filters": [
            "craftokai","craftoksecurity","chatfilter","[sanctionner]","(prism)","craftokia","----------",
            "informations sur","grade:","le joueur n'est pas banni !","] est banni :","banni par :","raison :","banni jusqu'à : ","ip ban : ", "Page:"
        ],
        "exclusive": True
    },
    "StaffChat": {
        "messages": [],
        "exclude_filters": [],
        "include_filters": ["[staffchat]"],
        "exclusive": True
    },
    "Reports": {
        "messages": [],
        "exclude_filters": [],
        "include_filters": ["[report]","[reports]","[report -","[reports -]"],
        "exclusive": True
    },
    "Sanctions": {
        "messages": [],
        "exclude_filters": ["historique de ce joueur est vide"],
        "include_filters": [
            "première fois","deuxième fois","première infraction","deuxième infraction","troisième infraction",
            "troisième fois","unmuted","unbanned","temp ip-","a banni temporairement","a débanni","a été banni par",
            "a été débanni par","a été réduit au silence par","a redonné la parole à","tempbanned",
            "a temporairement réduit au silence","a été kické par","a banni","a essayé de parler, mais il est réduit au silence",
            "a essayé de se connecter, mais il est banni","historique de", "est déjà réduit au silence, et vous n'avez pas la permission de remplacer", "est déjà banni, et vous n'avez pas la permission de remplacer"
        ],
        "exclusive": True
    },
}

hard_ignore_filters = [
    "Achat SMS","Parties personnalisées","Envie d'un grade ?","Débloquez des cosmétiques et des récompenses exclusives",
    "Heureux de te revoir","CRAFTOK - classement","Nous sommes ravis de t'accueillir sur Craftok !",
    "Profite de notre nouveau jeu duels et","accède à nos jeux avec le globe.","Boutique]","Jouer]","Paysafecard",
    "disponibles sur la boutique","grâce à nos différents grades dans la boutique",
    "Les classements sont maintenant disponibles !","Découvrez le classement des joueurs","Classement]",
    "Créez des parties incroyables avec","des fonctionnalités personnalisables exclusives",
    "Toute forme d'anti-jeu dont le fait de faire alliance avec d'autres joueurs est interdit, même en kitpvp.",
    "Le nouveau règlement est disponible sur le lien suivant :",
    "Merci d'en prendre connaissance, si vous jouez sur le kitpvp, les règles sont considérées comme acceptées",
    "Vous voulez soutenir Craftok","Envoyez HELLO au 83040","Puis entrez-le avec /code suivi du code","Et recevez 205 opales !",
    "+ Prix du SMS)","Discord]","Boutique - acheter des opales",
    "Vous n'avez pas assez d'opales pour effectuer","Votre achat ? Achetez-en sur la boutique !","Accès à la boutique ]",
    "Boutique - Acheter des pièces","Vous n'avez pas assez de pièces pour effectuer","Que vous obtenez avec le grade Legend/Hype",
    "Boutique - merci de votre achat","Votre achat de l'offre","Merci de votre achat et bon jeu sur Craftok!","Accès au discord ]", "CRAFTOK - Serveur Discord",
    "Soyez au courant des dernières nouvelles, événements", "et discussions de la communauté de Craftok", "en rejoignant notre serveur Discord !"
]

MINECRAFT_LOG = ""
OUTPUT_DIR = ""
html_path = ""
now = None
username = "Unknown"
version = "Unknown"
skin_url = ""
current_server = "Unknown"

def setup():
    """Lit/écrit la config, initialise username/version/skin/server, prépare le fichier HTML."""
    global MINECRAFT_LOG, OUTPUT_DIR, html_path, now, username, version, skin_url, current_server

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            MINECRAFT_LOG = config.get("MINECRAFT_LOG", "")
            OUTPUT_DIR = config.get("OUTPUT_DIR", "")
        except Exception as e:
            print(f"⚠️ Impossible de lire config.json : {e}")
            MINECRAFT_LOG, OUTPUT_DIR = "", ""
    else:
        open("Chat Logger/config.json", "x")
        MINECRAFT_LOG, OUTPUT_DIR = "", ""

    if not MINECRAFT_LOG or not os.path.isfile(MINECRAFT_LOG):
        while True:
            MINECRAFT_LOG = input("📂 Entrez le chemin complet du fichier latest.log : ").strip()
            if os.path.isfile(MINECRAFT_LOG):
                break
            print("❌ Fichier introuvable, réessayez.")

    if not OUTPUT_DIR or not os.path.isdir(OUTPUT_DIR):
        while True:
            OUTPUT_DIR = input("📂 Entrez le dossier où sauvegarder les logs HTML : ").strip()
            try:
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                break
            except Exception as e:
                print(f"❌ Impossible de créer le dossier : {e}, réessayez.")

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"MINECRAFT_LOG": MINECRAFT_LOG, "OUTPUT_DIR": OUTPUT_DIR}, f, indent=4, ensure_ascii=False)

    username_tmp, version_tmp, server_tmp = extract_info()
    username = username_tmp or "Unknown"
    version = version_tmp or "Unknown"
    current_server = server_tmp or "Unknown"
    skin_url = get_skin_url(username)

    now = datetime.datetime.now()
    html_filename = f"log_{now.strftime('%Y-%m-%d_%H-%M-%S')}.html"
    html_path = os.path.join(OUTPUT_DIR, html_filename)

    print(f"✅ Configuration prête.\n- Log Minecraft : {MINECRAFT_LOG}\n- Dossier de sortie : {OUTPUT_DIR}")

def minecraft_to_html(text: str) -> str:
    color_map = {"0":"#000000","1":"#0000AA","2":"#00AA00","3":"#00AAAA","4":"#AA0000","5":"#AA00AA",
                 "6":"#FFAA00","7":"#AAAAAA","8":"#555555","9":"#5555FF","a":"#55FF55","b":"#55FFFF",
                 "c":"#FF5555","d":"#FF55FF","e":"#FFFF55","f":"#FFFFFF", "t":"#888"}
    result = ""
    i = 0
    current_color = "#FFFFFF"
    while i < len(text):
        if text[i] == "§" and i + 1 < len(text):
            code = text[i + 1].lower()
            if code in color_map: current_color = color_map[code]
            i += 2
            continue
        result += f"<span style='color:{current_color}'>{text[i]}</span>"
        i += 1
    return result.replace("\n", "<br>")

def strip_minecraft_colors(text: str) -> str:
    return re.sub(r"§.", "", text)

def write_html_header(username, version, skin_url, current_server):
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="15">
<title>Chat Minecraft</title>
<style>
body {{ background-color:#1e1e1e;color:#f0f0f0;font-family:Consolas, monospace;margin:0;padding:0; }}
.header {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:10px 20px;
    background:#2c2c2c;
    box-shadow:0 0 8px rgba(0,0,0,0.4);
}}
.header-left {{
    display:flex;
    align-items:center;
    gap:10px;
}}
#skin {{
    width:32px;
    height:32px;
    border-radius:4px;
    transition: all 0.2s ease;
}}
#skin:hover {{
    transform: translateY(-3px);
    box-shadow:0 10px 20px rgba(0,0,0,0.6);
}}
#home {{
    transition: all 0.2s ease;
}}
#home:hover {{
    transform: translateY(-3px);
    box-shadow:0 10px 20px rgba(0,0,0,0.6);
}}
#username {{ font-weight:700; }}
.header-right {{
    display:flex;
    flex-direction:column;
    align-items:flex-end;
    gap:4px;
}}
h2 {{
    text-align:center;
    color:#aaa;
    margin:10px 0;
    flex:1;
}}
.tab {{
    margin:10px auto;
    border-radius:12px;
    background:#2b2b2b;
    box-shadow:0 0 8px rgba(0,0,0,0.4);
    width:80%;
}}
.tab-header {{
    cursor:pointer;
    padding:12px 15px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-weight:bold;
    box-shadow:0 0 6px rgba(0,0,0,0.5);
    transition: all 0.2s ease;
}}
.tab-header:hover {{
    transform: translateY(-3px);
    box-shadow:0 10px 20px rgba(0,0,0,0.6);
}}
.arrow {{ transition: transform 0.2s; }}
.tab-content {{ display:none; padding:10px 15px; }}
.message {{ margin:8px 0; white-space:pre-wrap; background:#232323; padding:10px 12px; border-radius:8px; transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease; border-left:4px solid transparent; }}
.message:hover {{ transform: translateY(-4px); box-shadow:0 10px 30px rgba(0,0,0,0.6); background:#151515; border-left-color:#444; }}
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
<script>
function openCategory(cat) {{
  let content = document.getElementById(cat + '_messages');
  if (!content) return;
  document.querySelectorAll('.tab-content').forEach(div => div.style.display = 'none');
  document.querySelectorAll('.arrow').forEach(arrowElem => arrowElem.textContent = '▶');
  content.style.display = 'block';
  const arrow = document.getElementById(cat + '_arrow');
  if (arrow) arrow.textContent = '▼';
  try {{ localStorage.setItem('openCat', cat); }} catch(e) {{}}
}}

function toggleCategory(cat) {{
  let content = document.getElementById(cat + '_messages');
  if (!content) return;
  if (content.style.display === 'block') {{
    content.style.display = 'none';
    const arrow = document.getElementById(cat + '_arrow');
    if (arrow) arrow.textContent = '▶';
    try {{ localStorage.removeItem('openCat'); }} catch(e) {{}}
  }} else {{
    openCategory(cat);
  }}
}}

window.addEventListener('DOMContentLoaded', function() {{
  try {{
    const saved = localStorage.getItem('openCat');
    if (saved) {{
      openCategory(saved);
    }} else {{
      pass;
    }}
  }} catch(e) {{}}

  try {{
    const y = parseInt(localStorage.getItem('scrollY') || '0', 10);
    if (!isNaN(y)) window.scrollTo(0, y);
  }} catch(e) {{}}
}});

window.addEventListener('beforeunload', function() {{
  try {{ localStorage.setItem('scrollY', window.scrollY); }} catch(e) {{}}
}});
let mybutton = document.getElementById("scrollTopBtn");

window.addEventListener("scroll", () => {{
  if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {{
    mybutton.classList.add("show");
  }} else {{
    mybutton.classList.remove("show");
  }}
}});

function topFunction() {{
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}
</script>
</head>
<body>
<div class="header">
  <div class="header-left">
    <a href="../logs_index.html"><img id="home" src="https://img.icons8.com/ios-filled/50/ffffff/home.png" alt="Retour Hub" style="width:28px;vertical-align:middle;margin-left:10px;cursor:pointer;"></a>
    <a href="https://fr.namemc.com/profile/{username}"><img id="skin" src="{skin_url}" alt="Voir le profil"></a>
    <span id="username">{username}</span>
  </div>
  <h2>Log du {now.strftime('%d/%m/%Y à %Hh%M')}</h2>
  <div class="header-right">
    <span id="version">Minecraft {version}</span>
    <span id="server">Server {current_server}</span>
  </div>
</div>

""")
        for cat, data in categories.items():
            f.write(f"""<div class="tab">
  <div class="tab-header" onclick="toggleCategory('{cat}')">
    <span>{cat}</span><span class="arrow" id="{cat}_arrow">▶</span>
  </div>
  <div class="tab-content" id="{cat}_messages"><!-- MESSAGES --></div>
</div>
""")
        f.write("""<!-- Bouton Remonter en Haut -->
<button onclick="topFunction()" id="scrollTopBtn" title="Remonter en haut">⬆</button>
</body></html>
""")
        print(f"➡  Création du fichier HTML: {html_path}")

def update_server_in_html(new_server: str):
    try:
        with open(html_path, "r+", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r'(<span id="server">).*?(</span>)', lambda m: m.group(1) + "Server " + new_server + m.group(2), content, flags=re.S)
            f.seek(0); f.write(content); f.truncate()
    except Exception as e:
        print(f"⚠️ Erreur update serveur: {e}")

def update_username_in_html(new_username: str):
    try:
        with open(html_path, "r+", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r'(<span id="username">).*?(</span>)', lambda m: m.group(1) + new_username + m.group(2), content, flags=re.S)
            f.seek(0); f.write(content); f.truncate()
    except Exception as e:
        print(f"⚠️ Erreur update username: {e}")

def update_version_in_html(new_version: str):
    try:
        with open(html_path, "r+", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r'(<span id="version">).*?(</span>)', lambda m: m.group(1) + "Minecraft " + new_version + m.group(2), content, flags=re.S)
            f.seek(0); f.write(content); f.truncate()
    except Exception as e:
        print(f"⚠️ Erreur update version: {e}")

def update_skin_in_html(new_skin_url: str):
    try:
        with open(html_path, "r+", encoding="utf-8") as f:
            content = f.read()
            content = re.sub(r'(<img\s+id="skin"\s+[^>]*src=")[^"]*(")', lambda m: m.group(1) + new_skin_url + m.group(2), content, flags=re.S)
            f.seek(0); f.write(content); f.truncate()
    except Exception as e:
        print(f"⚠️ Erreur update skin: {e}")

def add_message_to_category(category: str, timestamp: str, message: str):
    dt_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_message = f"<div class='message' data-datetime='{dt_now}'><span style='color:#888'>[{timestamp}]</span> {minecraft_to_html(message)}</div>\n"
    try:
        with open(html_path, "r+", encoding="utf-8") as f:
            content = f.read()
            pos = content.rfind(f'id="{category}_messages"')
            if pos != -1:
                insert_pos = content.find("<!-- MESSAGES -->", pos)
                if insert_pos != -1:
                    content = content[:insert_pos] + html_message + content[insert_pos:]
                    f.seek(0); f.write(content); f.truncate()
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du message: {e}")

def assign_message(timestamp, message):
    clean_message = strip_minecraft_colors(message).lower()

    if any(ignore.lower() in clean_message for ignore in hard_ignore_filters):
        return

    assigned = False
    for cat, data in categories.items():
        if cat == "Players":
            continue
        if data.get("exclusive", False):
            if any(tag.lower() in clean_message for tag in data.get("include_filters", [])) \
               and not any(tag.lower() in clean_message for tag in data.get("exclude_filters", [])):
                add_message_to_category(cat, timestamp, message)
                assigned = True
                break

    if not assigned:
        if not any(ex in clean_message for ex in categories["Players"].get("exclude_filters", [])):
            add_message_to_category("Players", timestamp, message)

def follow_log():
    global current_server, username, version, skin_url
    print("✅ Logger démarré. (CTRL + C pour arrêter)")
    pending_message = ""
    pending_timestamp = None

    timestamp_pattern = re.compile(r"\[\d{2}:\d{2}:\d{2}\]")
    re_connecting = re.compile(r"Connecting to\s+([^,]+)")
    re_user = re.compile(r"Setting user:\s*(\S+)")
    re_version = re.compile(r"Minecraft Version:\s*([^\s]+)")

    with open(MINECRAFT_LOG, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                line = line.rstrip()

                if "Connecting to" in line:
                    m = re_connecting.search(line)
                    if m:
                        new_server = m.group(1).strip()
                        if new_server and new_server != current_server:
                            current_server = new_server
                            update_server_in_html(current_server)

                if "Setting user:" in line:
                    m = re_user.search(line)
                    if m:
                        new_user = m.group(1).strip()
                        if new_user and new_user != username:
                            username = new_user
                            update_username_in_html(username)
                            new_skin = get_skin_url(username)
                            if new_skin and new_skin != skin_url:
                                skin_url = new_skin
                                update_skin_in_html(skin_url)

                if "Minecraft Version:" in line:
                    m = re_version.search(line)
                    if m:
                        new_version = m.group(1).strip()
                        if new_version and new_version != version:
                            version = new_version
                            update_version_in_html(version)

                if "[CHAT]" in line and current_server == "play.craftok.fr":
                    pending_timestamp = f"{datetime.datetime.now().strftime('%Y-%m-%d')} {line[1:9]}" if len(line) >= 9 else ""
                    pending_message = line.split("[CHAT]", 1)[1].lstrip()

                elif line.startswith("java.") or timestamp_pattern.match(line):
                    if pending_message:
                        assign_message(pending_timestamp, pending_message)
                    pending_message = ""
                    pending_timestamp = None

                elif pending_message:
                    pending_message += "\n" + "§t[" + pending_timestamp + "]§f " + line

        except KeyboardInterrupt:
            if pending_message:
                assign_message(pending_timestamp, pending_message)
            with open(html_path, "r+", encoding="utf-8") as f:
                content = f.read()
                pos = content.rfind("<meta http-equiv=\"refresh\" content=\"15\">")
                if pos != -1:
                    pos = pos
                    content = content[:pos-1] + content[pos+40:]
                    f.seek(0); f.write(content); f.truncate()
                
            os.system("python \"Chat Logger\\FullLogger.py\"")
            print("\n🛑 Logger arrêté.")

def extract_info():
    """Récupère pseudo + version depuis latest.log (scan complet au démarrage)."""
    username, version, server = "Unknown", "Unknown", "Unknown"
    try:
        with open(MINECRAFT_LOG, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "Setting user:" in line:
                    m = re.search(r"Setting user:\s*(\S+)", line)
                    if m:
                        username = m.group(1).strip()
                elif "Minecraft Version:" in line:
                    m = re.search(r"Minecraft Version:\s*([^\s]+)", line)
                    if m:
                        version = m.group(1).strip()
                elif "Connecting to" in line:
                    m = re.search(r"Connecting to ([^,]+), (\d+)", line)
                    if m:
                        server = m.group(1).strip()
    except Exception:
        pass
    return username, version, server

def get_skin_url(username):
    """Récupère l’URL du skin via Mojang + Crafatar."""
    if not username or username == "Unknown":
        return "https://crafatar.com/avatars/8667ba71b85a4004af54457a9734eed7?overlay"
    try:
        r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=5)
        if r.status_code == 200:
            uuid = r.json().get("id")
            if uuid:
                return f"https://crafatar.com/avatars/{uuid}?overlay"
    except Exception:
        pass
    return "https://crafatar.com/avatars/8667ba71b85a4004af54457a9734eed7?overlay"

if __name__ == "__main__":
    setup()
    write_html_header(username, version, skin_url, current_server)
    os.system("python \"Chat Logger\\logs_hub.py\"")
    os.system("python \"Chat Logger\\FullLogger.py\"")
    follow_log()
