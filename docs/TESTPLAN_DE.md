# Praxisprüfung vor Veröffentlichung

Die automatisierten Prüfungen ersetzen keinen mehrtägigen Betrieb mit der tatsächlichen DHL-Schnittstelle. Die folgenden Punkte sind vor der öffentlichen Katalogeinreichung abzuarbeiten.

## Installation und Alltag

- [ ] Backup der HA-Konfiguration erstellen, aktuelle HA-Version notieren.
- [ ] Beta installieren und über die Oberfläche einrichten; keinerlei DHL-Zugangsdaten eingeben.
- [ ] Adresse der gefundenen Station mit DHL abgleichen.
- [ ] Alle vier Fachgrößen und den Datenstand mit der Detailantwort vergleichen. „Viele frei“ auf der Website kann in der Integration eine genaue Zahl über fünf sein.
- [ ] Mindestens 48 Stunden beobachten: Datenstände, echte Änderungen, Ausfälle und Erholungen festhalten. Nicht schneller abfragen, um Änderungen zu erzwingen.
- [ ] Zwei weitere Stationen prüfen, darunter wenn möglich eine ohne Live-Daten. Unbekannte Werte dürfen niemals als 0 erscheinen.
- [ ] Oberfläche auf Deutsch und Englisch prüfen: Einrichtung, Optionen, Einheiten und Fehlertexte.
- [ ] Darstellung in hellem und dunklem Design einschließlich Icon prüfen.

## Lebenszyklus und Datenqualität

- [ ] HA neu starten: Station wird wieder geladen; Entity-IDs bleiben erhalten.
- [ ] Dieselbe Station erneut einrichten: verständlicher Abbruch statt Duplikat.
- [ ] Zweite Station hinzufügen: eigenständige Werte und Geräte.
- [ ] Altersgrenze ändern: neue Grenze wird nach dem Neuladen angewendet.
- [ ] Bei tatsächlich veraltetem Datenstand: Fachzahlen werden nicht verfügbar, Zeitstempel bleibt sichtbar und der Problemsensor meldet veraltete/fehlende Daten.
- [ ] In einer isolierten Testinstanz DHL-Verbindung unterbrechen und wiederherstellen. Erst unavailable, danach automatische Erholung. Keine Störung der produktiven HA-Installation für diesen Test erzeugen.
- [ ] Station entfernen: keine weiteren Abfragen, andere Station bleibt aktiv.
- [ ] Beta-Update und Rückkehr zur vorherigen Version testen, ohne Entity-IDs zu verlieren.

## Automatisiert abgedeckt

Einrichtung, doppelte Stationen, Eingabefehler, falscher Standort/Standorttyp, defekte Antworten, 204/404/403/429/5xx, Timeout, Verbindungsfehler, echte Nullwerte, einzelne ungültige Fachzahlen, fehlende Daten, Zeitstempel ohne Zeitzone, Zukunft, Ablauf exakt an der Altersgrenze, Wiederherstellung, ein gemeinsamer Poll je Station, Optionen-Neuladen und Aufräumen beim Entfernen. Diese Fehler werden über HTTP-Fixtures simuliert, ohne DHL absichtlich zu überlasten.

## Freigabekriterien

- Alle automatisierten Tests und beide offiziellen Repository-Prüfungen grün.
- Keine offenen Probleme, die alte, unbekannte oder fremde Stationsdaten als aktuell ausgeben.
- Installation, Neustart, Update und Entfernen praktisch bestätigt.
- Mindestens 48 Stunden Feldbetrieb dokumentiert; bei längeren DHL-Ausfällen entsprechend verlängern.
- Testergebnis und verbleibende Einschränkungen im Release dokumentiert.

Datum, HA-Version, Station, Beobachtung und Ergebnis gehören ins Testprotokoll. Keine Tokens, Cookies oder persönlichen Sendungsdaten anhängen.
