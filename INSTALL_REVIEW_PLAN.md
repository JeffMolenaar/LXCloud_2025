# LXCloud Install.sh Review en Fix Plan

## Gevonden Problemen in scripts/install.sh

### 1. **KRITIEK: Project Path Inconsistentie**
 - Script installeert naar `/home/lxcloud/LXCloud` 
- Maar gebruikt soms `project/` subdirectory en soms niet
- `debug_reporter.py` staat in `project/app/` maar systemd zoekt in `app/`
- **Fix**: Consistente pad structuur doorheen hele script

### 2. **Debug Directory Location**
 - Script maakt `/home/lxcloud/debug_queue` aan
- **Fix**: Al aangepast in debug scripts, moet nog in install.sh

### 3. **Systemd Service Issues**
- `Restart=always` veroorzaakt oneindige restart loops
- PATH environment incomplete
- ExecStart pad mogelijk incorrect
- **Fix**: Al aangepast in project/scripts/install.sh

### 4. **Missing Error Handling**
- Geen validatie of debug reporter files bestaan
- Geen check op virtual environment creation
- Database setup kan falen zonder goede error handling
- **Fix**: Toevoegen van validatie stappen

### 5. **Service User Permissions**
- `/home/lxcloud` directory wordt niet aangemaakt
- Debug queue permissions mogelijk incorrect
- **Fix**: Expliciete home directory setup

### 6. **MQTT Configuration**
- Mosquitto config niet aangepast voor LXCloud gebruik
- Default credentials/auth niet ingesteld
- **Fix**: Mosquitto configuratie toevoegen

## Immediate Action Plan

### Stap 1: Fix Project Structure (KRITIEK)
```bash
# Op server - fix de pad inconsistentie
sudo mkdir -p /opt/LXCloud/app
sudo mkdir -p /opt/LXCloud/scripts
sudo cp /opt/LXCloud/project/app/* /opt/LXCloud/app/ 2>/dev/null || true
sudo cp /opt/LXCloud/project/scripts/* /opt/LXCloud/scripts/ 2>/dev/null || true
sudo chown -R lxcloud:lxcloud /opt/LXCloud
```

### Stap 2: Debug Directory Setup
```bash
# Maak correcte debug directory
sudo mkdir -p /home/lxcloud/debug_queue
sudo chown lxcloud:lxcloud /home/lxcloud/debug_queue
sudo chmod 755 /home/lxcloud/debug_queue
```

### Stap 3: Service Files Update
- Systemd units aanpassen voor correcte paden
- Environment variables en PATH fixen
- Restart policy aanpassen

### Stap 4: Complete Install.sh Rewrite
- Consistente directory structuur
- Betere error handling
- Mosquitto configuratie
- Debug reporting volledig geïntegreerd

**Status**: Debug files aangepast, systemd template gefixt, diagnostics script aangemaakt.
**Volgende**: Install.sh volledig reviewen en critical path issues oplossen.