## Vooraf melden wat je wilt gaan aan passen voordat je dit doet. ik moet dit eerst goedkeuren.
 

## Reviews (belangrijk)
- **Focussen op**: leesbaarheid, foutafhandeling, edge cases, performance bij I/O.
- **Verboden patronen**: nested ternaries, `any`/`unknown` zonder narrowing, onnodige globale singletons.

## Documentatie
- Voeg JSDoc/docstrings toe voor publieke functies.
- Update `README` en `CHANGELOG` bij breaking changes.

## Schrijfstijl
- **Taal:** informele Nederlands is prima; houd het duidelijk en beknopt.
- **Toon:** direct.
- **Engels:** alleen als het technisch noodzakelijk is.


## Praktische regels
- Maak backups van bestanden voor veranderingen (bijv. `*_backup.html` in de backup map).
- Beperk wijzigingen tot wat nodig is; voorkom onnodige refactors.
- Testscripts en install-scripts leveren; de gebruiker of serverbeheerder voert ze uit.


- Geen Engelse antwoorden tenzij het echt niet anders kan.

## Debug/Tests
- Niet testen op de windows omgeving. wij doen dit op onze ubuntu LTS 24.04 server.
- Altijd commiten van changes zodat ik die weer kan pullen en installeren.