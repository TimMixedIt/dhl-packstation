# DHL Packstation – Installation

Version: **0.3.0**, benötigt **Home Assistant 2026.10.4 oder neuer**.

## Über Marketplace / HACS

In **HACS** nach **DHL Packstation** suchen und die Integration herunterladen. Ab Home Assistant 2026.11 findest du sie unter **Einstellungen → Marketplace**. Danach Home Assistant neu starten und unter **Einstellungen → Geräte & Dienste → Integration hinzufügen → DHL Packstation** deine Station einrichten.

## Manuell über ZIP

1. Ein Backup deiner Home-Assistant-Konfiguration erstellen.
2. Das Installations-ZIP entpacken.
3. Den enthaltenen Ordner `custom_components/dhl_packstation` in deinen HA-Konfigurationsordner kopieren. Der fertige Pfad muss `<HA-Konfigurationsordner>/custom_components/dhl_packstation/manifest.json` enthalten. Es darf kein zusätzlicher Unterordner `dhl-packstation` dazwischenliegen.
4. Home Assistant neu starten.
5. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **DHL Packstation** suchen.
6. Die Postleitzahl und Nummer der Station eingeben. Für die Umgebungssuche nur die PLZ eingeben und die Nummer freilassen.

Im DHL-Standortfinder gelistete DeinFach-Automaten richtest du ebenfalls mit Standort-PLZ und Stationsnummer ein. Freie Fächer werden angezeigt, soweit DHL aktuelle Zahlen meldet.

Die Integration erzeugt ein Gerät pro Station mit vier Fachzahlsensoren für S/M/L/XL, einer Gesamtzahl und zwei Diagnosewerten: DHL-Datenstand und „DHL-Daten veraltet oder fehlend“. Weitere Stationen werden durch erneutes Hinzufügen der Integration eingerichtet.

## Die mitgelieferten Karten

Nach der Einrichtung den Browser einmal neu laden. Dann im Dashboard „Bearbeiten → Karte hinzufügen“ öffnen:

- **DHL Packstation · Freie Fächer** für die Darstellung einer Station wie im DHL-Bild.
- **DHL Packstation · Mehrere Stationen** für den Vergleich mehrerer Stationen.

Die Karte im visuellen Editor auswählen und die Station(en) einstellen. In der Übersicht kannst du die ausgewählten Stationen mit den Pfeiltasten nach oben oder unten verschieben. Die Karte übernimmt die Reihenfolge aus der `stations`-Liste, auch bei bereits bestehenden Listen. Ohne Auswahl zeigt die Übersicht alle eingerichteten Stationen, sortiert nach Postleitzahl und dann nach Stationsnummer. „Genaue Fachzahlen anzeigen“ ersetzt „viele frei“ durch die konkrete Zahl. Ein Klick auf eine Fachgröße öffnet deren Sensorinformationen. Es ist kein zusätzliches Karten-Repository und kein manueller Ressourceneintrag nötig. Vorhandene Dashboards werden nicht automatisch verändert.

Die Mehrstationskarte zeigt die freien Fächer je Größe in einer Zeile pro Station. Tippe auf einen Stationsnamen für Adresse, Aktualisierungszeit und Route. Im **Paketalarm** siehst du schon beim Eingeben, welche Station zum Beispiel **1× S und 2× M** aufnehmen kann und welche Fächer noch fehlen.

Wähle für einen Alarm die Stationen aus und drücke **Suche starten**. **HA-Glocke (ohne Push)** legt die Meldung in der Home-Assistant-Glocke ab. Für eine Push-Nachricht wählst du ein Gerät mit eingerichteter Home-Assistant-App und erlaubten Benachrichtigungen. Der Alarm meldet sich einmal, sobald eine ausgewählte Station für alle eingegebenen Pakete gleichzeitig passende Fächer meldet. Steuerung und Einrichtung erfordern ein HA-Administratorkonto.

Die Routenlinks öffnen **Apple Karten** oder **Google Maps**. **Standorte auf der Karte** zeigt die Standorte gemeinsam in Home Assistant. Der **Wochentrend** in der Einzelkarte beruht auf den eigenen Messungen der letzten acht Wochen. Für jeden Wochentag erscheinen Zahl und Farbe ab zwei beobachteten Tagen. Die Fachsensoren unterstützen außerdem die Langzeitstatistik des HA-Recorders.

Die Abfrage erfolgt gemeinsam alle 15 Minuten. Unter den Optionen kannst du das maximale Alter der DHL-Daten festlegen. Standard sind 60 Minuten. Danach werden Fachzahlen nicht verfügbar, bis DHL wieder hinreichend aktuelle Daten liefert. Ein echter Nullwert bedeutet dagegen, dass DHL null freie Fächer dieser Größe gemeldet hat.

Falls du das frühere YAML-Beispiel installiert hast: Nach erfolgreichem Vergleich die dortigen REST-Sensoren selbst entfernen, wenn du sie nicht mehr brauchst. Sie werden nicht automatisch übernommen oder gelöscht.

Für ein Update den bisherigen Komponentenordner sichern, durch den neuen ersetzen und HA neu starten. Bei Problemen den gesicherten Ordner zurückkopieren und erneut starten. Zum Entfernen zuerst die Integrationseinträge in HA löschen, dann den Komponentenordner entfernen und HA neu starten.

Die Integration ist im allgemeinen HACS-/Marketplace-Katalog enthalten. Verbleibende praktische Prüfungen stehen im [Testplan](TESTPLAN_DE.md).
