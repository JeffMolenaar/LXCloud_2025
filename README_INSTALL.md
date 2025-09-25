# LXCloud - Installatiehandleiding (test op Ubuntu 24.04 LTS)

## Doel

Deze gids beschrijft hoe je de repository kloont en de installer `scripts/install.sh` uitvoert op een Ubuntu 24.04 testserver.

## Belangrijk

- Draai dit alleen op een test- of staging-VM, niet op kritieke productie-machines.
- De installer installeert system packages (MariaDB, Mosquitto, Nginx, enz.).
- Voor automatische, niet-interactieve runs, gebruik de vlag `--yes`.
- De create_app smoke-test is opt-in via `--run-smoke` (standaard uit).

## Voorwaarden

- Ubuntu 24.04 LTS (of 22.04).
- Root toegang (sudo).
- (Optioneel) een GitHub token als je de debug-report pusher wilt gebruiken: export GITHUB_TOKEN=...

## Stappen (kort)

1. Clone repository op de server:

```bash
git clone https://github.com/JeffMolenaar/LXCloud_2025.git /home/lxcloud/LXCloud
cd /home/lxcloud/LXCloud
```

2. Voer de installer uit (interactief):

```bash
sudo ./scripts/install.sh
```

3. Voor een geautomatiseerde test-run (non-interactive):

```bash
sudo ./scripts/install.sh --yes
```

4. Optioneel: run de create_app smoke-test na dependency install:

```bash
sudo ./scripts/install.sh --yes --run-smoke
```

## Aanbevolen environment variabelen

- MYSQL_ROOT_PASSWORD (indien root DB-auth vereist tijdens DB setup)
- GITHUB_TOKEN (indien je automatische debug report push wilt inschakelen)

## Verdere troubleshooting

- Bekijk journalctl voor service logs: `journalctl -u lxcloud -f`
- Bekijk Nginx config test: `nginx -t`
- Als de installer faalt, bekijk de output en her-run met `--yes` wanneer je zeker bent van de keuzes.

## Veiligheid

- De installer gebruikt `DEBIAN_FRONTEND=noninteractive` wanneer `--yes` wordt opgegeven.
- Wijzig standaardwachtwoorden en secret keys na installatie.

## Contact

Als je problemen tegenkomt, kopieer de foutoutput en open een issue in de repository of stuur de output naar de verantwoordelijke dev.
