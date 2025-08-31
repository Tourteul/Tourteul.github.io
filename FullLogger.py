import os
import re
import sys
import json
import datetime
from typing import List, Dict, Optional

CONFIG_FILE = r"Chat Logger\\config.json"
OUTPUT_FILENAME = "logs.html"
jours_a_verifier = 3

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Config introuvable : {CONFIG_FILE}")

def ask_path(prompt: str, default: str) -> str:
    print(f"{prompt} (Entrée pour utiliser le chemin par défaut: {default})")
    resp = input("> ").strip()
    return resp or default

def find_html_files(folder: str) -> List[str]:
    files = []
    for name in os.listdir(folder):
        dates_a_verifier = [
            (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d_")
            for i in range(jours_a_verifier)
        ]
        if name.lower().endswith(".html") and  any(date_prefix in name for date_prefix in dates_a_verifier):
            files.append(os.path.join(folder, name))
    files.sort()
    return files

def parse_messages_from_html(content: str, source_file: str) -> List[Dict]:
    """
    Extrait toutes les <div class='message' data-datetime='...'>...</div>
    Retourne liste de dict: { 'dt': datetime, 'dt_str': str, 'html': inner_html, 'text': stripped_text, 'file': source_file }
    """
    results = []

    pattern = re.compile(r"<div\b([^>]*)\bclass=['\"]message['\"][^>]*>(.*?)</div>", re.IGNORECASE | re.DOTALL)
    for m in pattern.finditer(content):
        inner = m.group(2).strip()

        dt_str = None
        dt_match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", inner)
        if dt_match:
            dt_str = dt_match.group(1).strip()

        plain = re.sub(r"<[^>]+>", "", inner)
        plain = plain.replace("\xa0", " ").strip()
        inner = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', inner).strip()

        results.append({
            "dt_str_raw": dt_str,
            "html": inner,
            "text": plain,
            "file": source_file
        })

    return results

def normalize_datetime(dt_raw: Optional[str]):
    """
    Normalise dt_raw en datetime object et string 'YYYY-MM-DD HH:MM:SS'.
    Si dt_raw est None, utilise fallback_date (généralement la date du fichier).
    Si dt_raw est du format HH:MM:SS, le combine avec fallback_date.date().
    """

    dt_raw = dt_raw.strip()
    try:
        dt = datetime.datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
        return dt, dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

def aggregate_logs(logs_dir: str, out_path: str):
    files = find_html_files(logs_dir)
    if not files:
        print("Aucun fichier HTML trouvé dans", logs_dir)
        return

    all_entries: List[Dict] = []

    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
        except Exception as e:
            print(f"⚠️ Impossible de lire {file}: {e}")
            continue

        entries = parse_messages_from_html(content, os.path.basename(file))
        for e in entries:
            dt_raw = e.get("dt_str_raw")
            dt_obj, dt_str = normalize_datetime(dt_raw)
            e["dt"] = dt_obj
            e["dt_str"] = dt_str
            all_entries.append(e)

    all_entries.sort(key=lambda x: (x.get("dt") or datetime.datetime.min), reverse=True)

    now = datetime.datetime.now().strftime("%d/%m/%Y à %Hh%M")
    total = len(all_entries)
    earliest = all_entries[0]["dt_str"] if total else "N/A"
    latest = all_entries[-1]["dt_str"] if total else "N/A"

    html_head = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>All Logs</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ background-color:#1e1e1e;color:#f0f0f0;font-family:Consolas, monospace;margin:0;padding:0; }}
.container {{ max-width:1100px;margin:0 auto;padding:16px; }}
.header {{ display:flex; align-items:center; gap:16px; justify-content:space-between; border-radius:8px; background:#2c2c2c; padding:12px 16px; border-bottom:1px solid #333; }}
.header .title {{ font-weight:700; }}
.info {{ color:#bbb; font-size:0.9em; padding-left: 3.2em; padding-top: 0.5em;}}
.search-bar {{ display:flex; gap:8px; align-items:center; padding:12px 0; background:transparent; flex-wrap:wrap; }}
.search-bar input[type="text"], .search-bar input[type="datetime-local"] {{ padding:6px 8px;border-radius:6px;border:1px solid #444;background:#1e1e1e;color:#eee; }}
.search-bar button {{ padding:6px 10px;border-radius:6px;border:1px solid #444;background:#333;color:#eee;cursor:pointer; transition: transform 0.2s ease;}}
.search-bar button:hover {{
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
.tab {{ margin-top:12px; border-radius:8px; background:#2b2b2b; padding:12px; box-shadow:0 0 8px rgba(0,0,0,0.4); }}
.messages {{ margin-top:8px; }}
.message {{ margin:8px 0; white-space:pre-wrap; background:#232323; padding:10px 12px; border-radius:8px; transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease; border-left:4px solid transparent; }}
.message:hover {{ transform: translateY(-4px); box-shadow:0 10px 30px rgba(0,0,0,0.6); background:#151515; border-left-color:#444; }}
.meta {{ color:#888; font-size:0.9em; margin-right:8px; }}
.hidden {{ display:none !important; }}
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
function parseDTattr(dt) {{
  if (!dt) return null;
  try {{ return new Date(dt.replace(' ', 'T')); }} catch(e){{ return null; }}
}}

function exportVisibleTxt() {{
    const msgs = Array.from(document.querySelectorAll('.message'))
        .filter(m => m.style.display !== 'none' && getComputedStyle(m).display !== 'none');
    if (!msgs.length) {{
        alert('Aucun message visible à exporter.');
        return;
    }}
    const header = "+----------------+\\n|      LOGS      |\\n+----------------+ \\n \\n";
    const lines = msgs.map(m => (m.innerText || m.textContent || '').trim());
    const content = header + lines.join("\\n\\n");

    const now = new Date();
    const pad = n => n.toString().padStart(2, '0');
    const ts = now.getFullYear().toString() + pad(now.getMonth()+1) + pad(now.getDate()) +
               '_' + pad(now.getHours()) + pad(now.getMinutes()) + pad(now.getSeconds());
    const filename = 'export_' + ts + '.txt';

    const blob = new Blob([content], {{type: 'text/plain;charset=utf-8'}});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
}}

document.addEventListener('DOMContentLoaded', function() {{
    const btn = document.getElementById('btn_export_txt');
    if (btn) btn.addEventListener('click', exportVisibleTxt);
}});

function getSavedFilters() {{
  try {{
    return {{
      start: localStorage.getItem('agg_search_start') || '',
      end: localStorage.getItem('agg_search_end') || '',
      pseudo: localStorage.getItem('agg_search_pseudo') || '',
      text: localStorage.getItem('agg_search_text') || ''
    }};
  }} catch (e) {{ return {{start:'',end:'',pseudo:'',text:''}}; }}
}}

function applySearch() {{
  const start = document.getElementById('search_start').value;
  const end = document.getElementById('search_end').value;
  const pseudo = document.getElementById('search_pseudo').value.trim().toLowerCase();
  const text = document.getElementById('search_text').value.trim().toLowerCase();

  if (start || end || pseudo || text) {{ window.disablePagination && window.disablePagination(); }}
  else {{ window.enablePagination && window.enablePagination(); }}


  try {{
    localStorage.setItem('agg_search_start', start);
    localStorage.setItem('agg_search_end', end);
    localStorage.setItem('agg_search_pseudo', pseudo);
    localStorage.setItem('agg_search_text', text);
  }} catch(e){{}}

  const startDate = start ? new Date(start) : null;
  const endDate = end ? new Date(end) : null;

  const msgs = document.querySelectorAll('.message');
  msgs.forEach(msg => {{
    let visible = true;

    const dtAttr = msg.getAttribute('data-datetime');
    if (dtAttr && (startDate || endDate)) {{
      const mDate = parseDTattr(dtAttr);
      if (mDate) {{
        if (startDate && mDate < startDate) visible = false;
        if (endDate && mDate > endDate) visible = false;
      }}
    }}

    const txt = (msg.innerText || msg.textContent || '').toLowerCase();
    if (visible && pseudo) {{
      if (!txt.includes(pseudo)) visible = false;
    }}
    if (visible && text) {{
      if (!txt.includes(text)) visible = false;
    }}

    msg.style.display = visible ? '' : 'none';
  }});

  const tab = document.getElementById('alltab');
  if (!tab) return;
  const anyVisible = Array.from(tab.querySelectorAll('.message')).some(m => m.style.display !== 'none');
  tab.style.display = anyVisible ? '' : 'none';
}}

function clearSearch() {{ 
  document.getElementById('search_start').value = ''; 
  document.getElementById('search_end').value = ''; 
  document.getElementById('search_pseudo').value = ''; 
  document.getElementById('search_text').value = ''; 
  try {{ 
    localStorage.removeItem('agg_search_start'); 
    localStorage.removeItem('agg_search_end'); 
    localStorage.removeItem('agg_search_pseudo'); 
    localStorage.removeItem('agg_search_text'); 
  }} catch(e){{}} 
  applySearch(); 
  initPagination(200);
}}

document.addEventListener('DOMContentLoaded', function() {{
  try {{
    const saved = getSavedFilters();
    if (saved.start) document.getElementById('search_start').value = saved.start;
    if (saved.end) document.getElementById('search_end').value = saved.end;
    if (saved.pseudo) document.getElementById('search_pseudo').value = saved.pseudo;
    if (saved.text) document.getElementById('search_text').value = saved.text;
  }} catch(e){{}}

  ['search_start','search_end','search_pseudo','search_text'].forEach(id => {{
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', applySearch);
    el.addEventListener('input', function() {{
      if (window._agg_timeout) clearTimeout(window._agg_timeout);
      window._agg_timeout = setTimeout(applySearch, 350);
    }});
  }});

  document.getElementById('btn_clear').addEventListener('click', clearSearch);

  applySearch();
}});
function copyMessage(el) {{
  let clone = el.cloneNode(true);
  clone.querySelectorAll("button").forEach(b => b.remove());
  let text = (clone.innerText || clone.textContent || "").trim();
  text = text.replace(/\\p{{Extended_Pictographic}}/gu, "");
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {{
    el.style.backgroundColor = "#004400";
    setTimeout(() => el.style.backgroundColor = "", 400);
  }}).catch(err => console.error("Erreur de copie:", err));
}}
function addCopyButton(msg) {{
  if(msg.querySelector(".copy-btn")) return;
  const btn = document.createElement("button");
  btn.className = "copy-btn";
  btn.textContent = "📋";
  btn.style.cssText = "float:right;background:#3a3a3a;border:none;color:#fff;border-radius:50%;cursor:pointer;padding:4px;margin-left:8px;box-shadow:0 4px 6px rgba(0,0,0,0.4);";
  btn.title = "Copier ce message";
  btn.addEventListener("click", (e)=>{{ e.stopPropagation(); copyMessage(msg); }});
  msg.appendChild(btn);
}}

// ----- PAGINATION -----
function initPagination(perPage){{
  window._perPage = perPage || 200;
  window._renderedCount = 0;
  window._paginationEnabled = true;
  window._allMessages = Array.from(document.querySelectorAll('.message'));
  window._allMessages.forEach(m => m.style.display='none');
  _renderNextChunk();
  if(!window._paginationHandlerInstalled){{
    window._paginationHandlerInstalled=true;
    window.addEventListener('scroll',()=>{{
      if(!window._paginationEnabled) return;
      const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 200;
      if(nearBottom) _renderNextChunk();
    }},{{passive:true}});
  }}
}}

window._renderNextChunk=function(){{
  if(!window._allMessages) return;
  let start = window._renderedCount || 0;
  if(start >= window._allMessages.length) return;
  let end = Math.min(start + (window._perPage||500), window._allMessages.length);
  for(let i=start;i<end;i++){{
    let msg = window._allMessages[i];
    msg.style.display='';
    addCopyButton(msg);
  }}
  window._renderedCount=end;
}};

window.disablePagination=function(){{ window._paginationEnabled=false; }};
window.enablePagination=function(){{
  window._paginationEnabled=true;
  if(!window._allMessages) return;
  const someVisible = window._allMessages.some(m=>m.style.display!=='none');
  if(!someVisible){{ window._renderedCount=0; _renderNextChunk(); }}
}};

document.addEventListener("DOMContentLoaded",()=>{{
  initPagination(200); 
  let mybutton = document.getElementById("scrollTopBtn");

  window.addEventListener("scroll", () => {{
    if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {{
      mybutton.classList.add("show");
    }} else {{
      mybutton.classList.remove("show");
    }}
  }});
}});

function topFunction() {{
  window.scrollTo({{ top: 0, behavior: 'smooth' }});

  function check() {{
    if (window.scrollY === 0) {{
      clearSearch();
    }} else {{
      requestAnimationFrame(check);
    }}
  }}
  requestAnimationFrame(check);
}}
</script>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <div class="title">
        <a href="logs_index.html"><img id="home" src="https://img.icons8.com/ios-filled/50/ffffff/home.png" alt="Retour Hub" style="width:28px;vertical-align:middle;margin-left:10px;cursor:pointer;"></a>
        All the Logs
      </div>
      <div class="info">Généré: {now} — Entrées: {total} — période: {earliest} → {latest}</div>
    </div>
  </div>

  <div class="search-bar">
    <input type="datetime-local" id="search_start" title="Début (date+heure)">
    <input type="datetime-local" id="search_end" title="Fin (date+heure)">
    <input type="text" id="search_pseudo" placeholder="Pseudo (ou portion)" title="Rechercher par pseudo">
    <input type="text" id="search_text" placeholder="Texte / mot-clé" title="Rechercher dans le message">
    <button id="btn_clear">Effacer</button>
    <button id="btn_export_txt">Exporter TXT</button>
  </div>

  <div id="alltab" class="tab">
    <div class="messages">
"""

    html_tail = """
    </div>
  </div>
</div>
<button onclick="topFunction()" id="scrollTopBtn" title="Remonter en haut">⬆</button>
</body>
</html>
"""

    try:
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(html_head.format(now=now, total=total, earliest=earliest, latest=latest, logs_dir=logs_dir.replace("\\", "\\\\")))
            for e in all_entries:
                dt_attr = e.get("dt_str", "")
                inner_html = e.get("html", "")
                msg_html = f"<div class='message' data-datetime='{dt_attr}'>{inner_html}</div>\n"
                out.write(msg_html)
            out.write(html_tail)
        print(f"✅ Page générée: {out_path} ({total} entrées)")
    except Exception as e:
        print("❌ Erreur lors de la génération du fichier HTML:", e)

def main():
    config = load_config()
    logs_dir = config.get("OUTPUT_DIR", "")
    if not logs_dir or not os.path.isdir(logs_dir):
        print(f"Chemin par défaut introuvable: {logs_dir}")
        sys.exit(1)

    out_path = "Chat Logger\\" + OUTPUT_FILENAME
    aggregate_logs(logs_dir, out_path)

if __name__ == "__main__":
    main()
