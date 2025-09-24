
LXCloud Installer Test Plan
==========================

Doel: Verifieer dat `scripts/install.sh` op een schone Ubuntu 24.04 LTS-machine werkt, inclusief optionele MariaDB-installatie en automatische database/user-setup.

Voorwaarden:

- Schone Ubuntu Server 24.04 VM met netwerk en sudo-toegang.
- SSH-toegang en minimaal 2 GB RAM.

Stappen:

1) Kopieer repository naar de VM

   Kopieer de gehele projectmap (bijv. met `rsync -a`) of clone de repo.

   ```bash
   rsync -a --progress . user@vm:/home/user/lxcloud
   ```

2) Maak het script uitvoerbaar en start de installatie (MariaDB via socket-auth)

   Voer uit als root of via sudo. Als MariaDB root gebruik via socket werkt (standaard Ubuntu), niets extra nodig:

   ```bash
   sudo bash /home/user/lxcloud/scripts/install.sh
   ```

3) Test met expliciet root-wachtwoord (voor setups met root password)

   Als MariaDB root heeft gekregen een wachtwoord tijdens installatie, geef dit door:

   ```bash
   sudo MYSQL_ROOT_PASSWORD='RootPass123!' bash /home/user/lxcloud/scripts/install.sh
   ```

4) Validatie na installatie

   - Controleer services:

     ```bash
     systemctl status lxcloud
     systemctl status mariadb
     systemctl status mosquitto
     ```

   - Controleer dat de webserver reageert (op poort 80):

     ```bash
     curl -I http://localhost/
     ```

   - Controleer database en gebruiker:

     ```bash
     mysql -u lxcloud -p -e "SELECT User,Host FROM mysql.user WHERE User='lxcloud'"
     ```

   - Controleer dat de application logs bestaan:

     ```bash
     ls -la /var/log/lxcloud/
     ```

5) Foutafhandeling en veelvoorkomende problemen

   - Als de scriptstap voor het creëren van database/user faalt: voer handmatig de SQL die het script printte uit met `mysql -u root -p`.
   - Als Python dependencies falen tijdens `pip install`, controleer of build tools (`build-essential`, `python3-dev`, `default-libmysqlclient-dev`) zijn geïnstalleerd en probeer opnieuw.

6) Herhaalbaarheid

   - Het script is idempotent voor database en gebruiker (CREATE IF NOT EXISTS). Je kunt het meerdere keren draaien.

7) Extra aanbevelingen

   - Voor productie: gebruik een geheimenmanager voor `MYSQL_ROOT_PASSWORD` en `DB` credentials. Voorkom het tonen van standaard-credentials tijdens installatie.

